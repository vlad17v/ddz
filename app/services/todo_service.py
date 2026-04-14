import os
import re
import sys
from collections import Counter
from datetime import datetime

from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status

from app.core.config import settings
from app.models.db import TodoDB
from app.models.schemas import Tags
from app.models.schemas import TodoExportRow
from app.models.schemas import TodoSource
from app.models.schemas import WordFrequency
from app.repositories.todo_repository import TodoRepository
from app.repositories.todo_search_repository import TodoSearchRepository
from app.utils.excel import export_todos
from app.utils.excel import import_todos
from app.utils.files import delete_file_if_exists
from app.utils.files import delete_image
from app.utils.files import extract_text_from_path
from app.utils.files import generate_random_filename
from app.utils.files import get_extension
from app.utils.files import hash_upload_file
from app.utils.files import load_image
from app.utils.files import save_upload_file
from app.utils.gitlab import get_todos_by_issues

LOCAL_STOP_WORDS = {
    "а",
    "без",
    "был",
    "бы",
    "была",
    "были",
    "было",
    "быть",
    "в",
    "вам",
    "вас",
    "весь",
    "во",
    "вот",
    "все",
    "всего",
    "всех",
    "вы",
    "где",
    "да",
    "даже",
    "для",
    "до",
    "его",
    "ее",
    "ей",
    "если",
    "есть",
    "еще",
    "же",
    "за",
    "здесь",
    "и",
    "из",
    "или",
    "им",
    "их",
    "к",
    "как",
    "ко",
    "когда",
    "кто",
    "ли",
    "либо",
    "мне",
    "может",
    "мы",
    "на",
    "над",
    "не",
    "него",
    "нее",
    "нет",
    "ни",
    "них",
    "но",
    "о",
    "об",
    "однако",
    "около",
    "он",
    "она",
    "они",
    "оно",
    "от",
    "очень",
    "по",
    "под",
    "при",
    "с",
    "со",
    "так",
    "также",
    "такой",
    "там",
    "те",
    "тем",
    "то",
    "того",
    "тоже",
    "той",
    "только",
    "том",
    "ты",
    "у",
    "уже",
    "хотя",
    "чего",
    "чей",
    "чем",
    "что",
    "чтобы",
    "эта",
    "эти",
    "это",
    "я",
    "дима",
    "артем",
    "сергей",
}

SECRECY_REPLACEMENTS = {
    "совершенно секретно": "неинтересно",
    "для служебного пользования": "неинтересно",
    "конфиденциально": "неинтересно",
    "секретно": "неинтересно",
}

WORD_PATTERN = re.compile(r"[a-zA-Zа-яА-ЯёЁ-]+")


class TodoService:
    def __init__(self, todo_repo: TodoRepository, search_repo: TodoSearchRepository):
        self.todo_repo = todo_repo
        self.search_repo = search_repo

    async def _build_search_document(self, todo: TodoDB) -> dict:
        attachment_text = extract_text_from_path(todo.attachment_path)
        return {
            "id": todo.id,
            "title": todo.title,
            "details": todo.details,
            "tag": todo.tag,
            "source": todo.source,
            "created_at": todo.created_at.isoformat() if todo.created_at else None,
            "attachment_name": os.path.basename(todo.attachment_path) if todo.attachment_path else None,
            "attachment_text": attachment_text,
        }

    async def _sync_to_search(self, todo: TodoDB) -> None:
        document = await self._build_search_document(todo)
        await self.search_repo.index_todo(todo.id, document)

    @staticmethod
    def _collect_texts(todo: TodoDB) -> list[str]:
        parts = [todo.title, todo.details, extract_text_from_path(todo.attachment_path)]
        return [part.strip() for part in parts if part and part.strip()]

    @staticmethod
    def _is_countable_word(word: str) -> bool:
        normalized = word.strip("-").lower()
        return len(normalized) >= 3 and normalized not in LOCAL_STOP_WORDS and bool(WORD_PATTERN.fullmatch(normalized))

    def _normalize_texts_locally(self, texts: list[str]) -> list[str]:
        normalized_text = "\n".join(texts).lower()
        for source, target in SECRECY_REPLACEMENTS.items():
            normalized_text = normalized_text.replace(source, target)
        return [
            word.strip("-").lower()
            for word in WORD_PATTERN.findall(normalized_text)
            if self._is_countable_word(word)
        ]

    async def get_top_words(self, *, limit: int = 10) -> list[WordFrequency]:
        todos = await self.todo_repo.get_all_todos()
        texts: list[str] = []
        for todo in todos:
            texts.extend(self._collect_texts(todo))

        if not texts:
            return []

        analyzed_words = await self.search_repo.analyze_texts(texts)
        if analyzed_words:
            words = [word for word in analyzed_words if self._is_countable_word(word)]
        else:
            words = self._normalize_texts_locally(texts)

        counts = Counter(words)
        return [WordFrequency(word=word, count=count) for word, count in counts.most_common(limit)]

    async def _save_image(self, image: UploadFile | None) -> tuple[str | None, str | None]:
        if not image or not image.filename:
            return None, None
        image_hash = await hash_upload_file(image)
        duplicate_path = await self.todo_repo.find_duplicate_image_path(image_hash)
        if duplicate_path:
            return duplicate_path, image_hash
        filename = f"{generate_random_filename()}.{get_extension(image.filename)}"
        await load_image(image, filename)
        return filename, image_hash

    async def _save_attachment(self, attachment: UploadFile | None) -> str | None:
        if not attachment or not attachment.filename:
            return None
        filename = f"{generate_random_filename()}.{get_extension(attachment.filename)}"
        destination = os.path.join(settings.ATTACHMENTS_DIR, filename)
        await save_upload_file(attachment, destination)
        return destination

    async def list_todos(
        self,
        *,
        limit: int,
        skip: int,
        creation_date_start: datetime | None,
        creation_date_end: datetime | None,
        tag: Tags | None,
        query: str | None,
    ) -> tuple[list[TodoDB], int]:
        search_result = None
        if query or tag or creation_date_start or creation_date_end:
            search_result = await self.search_repo.search_todos(
                query=query,
                tag=tag.value if tag else None,
                creation_date_start=creation_date_start,
                creation_date_end=creation_date_end,
                skip=skip,
                limit=limit,
            )
        if search_result is not None:
            todos = await self.todo_repo.get_todos_by_ids(search_result["ids"])
            return todos, int(search_result["total"])

        todos = await self.todo_repo.get_todos(
            limit=limit,
            skip=skip,
            creation_date_start=creation_date_start,
            creation_date_end=creation_date_end,
            tag=tag,
            text_query=query,
        )
        count = await self.todo_repo.get_count_todos(
            creation_date_start=creation_date_start,
            creation_date_end=creation_date_end,
            tag=tag,
            text_query=query,
        )
        return todos, count

    async def create_todo(
        self,
        *,
        title: str,
        details: str,
        tag: Tags,
        source: TodoSource,
        count_todos: int,
        image: UploadFile | None,
    ) -> list[TodoDB]:
        if count_todos < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="count_todos must be greater than 0")
        image_path, image_hash = await self._save_image(image)
        created_todos: list[TodoDB] = []
        for index in range(1, count_todos + 1):
            todo = TodoDB(
                title=f"{title} {index}" if count_todos > 1 else title,
                details=details,
                tag=tag.value,
                source=source.value,
                image_path=image_path,
                image_hash=image_hash,
            )
            await self.todo_repo.add_todo(todo)
            created_todos.append(todo)

        await self.todo_repo.commit()
        for todo in created_todos:
            await self._sync_to_search(todo)
        return created_todos

    async def get_todo(self, todo_id: int) -> TodoDB:
        todo = await self.todo_repo.get_todo(todo_id)
        if not todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Not found todo by this id: {todo_id}",
            )
        return todo

    async def update_todo(
        self,
        *,
        todo_id: int,
        title: str,
        details: str,
        completed: bool,
        tag: Tags,
        created_at: datetime | None,
        image_path: str | None,
        existing_image: str | None,
        image: UploadFile | None,
        attachment: UploadFile | None,
    ) -> TodoDB:
        todo = await self.get_todo(todo_id)
        next_image_path = image_path
        next_image_hash = todo.image_hash

        if image and image.filename:
            next_image_path, next_image_hash = await self._save_image(image)
            if next_image_path != todo.image_path and not await self.todo_repo.get_other_todo_by_image_path(todo.image_path, todo.id):
                await delete_image(todo.image_path)
        elif existing_image:
            existing_todo = await self.todo_repo.get_other_todo_by_image_path(existing_image, todo.id)
            next_image_path = existing_image
            next_image_hash = existing_todo.image_hash if existing_todo else todo.image_hash
            if next_image_path != todo.image_path and not await self.todo_repo.get_other_todo_by_image_path(todo.image_path, todo.id):
                await delete_image(todo.image_path)

        next_attachment_path = todo.attachment_path
        if attachment and attachment.filename:
            if todo.attachment_path:
                delete_file_if_exists(todo.attachment_path)
            next_attachment_path = await self._save_attachment(attachment)

        data = {
            "title": title,
            "details": details,
            "completed": completed,
            "tag": tag.value,
            "created_at": created_at or todo.created_at,
            "completed_at": datetime.utcnow() if completed else None,
            "image_path": next_image_path,
            "image_hash": next_image_hash,
            "source": todo.source,
            "attachment_path": next_attachment_path,
        }
        await self.todo_repo.update_todo(todo_id, data)
        await self.todo_repo.commit()
        updated_todo = await self.get_todo(todo_id)
        await self._sync_to_search(updated_todo)
        return updated_todo

    async def delete_todo(self, todo_id: int) -> None:
        todo = await self.get_todo(todo_id)
        if not await self.todo_repo.get_other_todo_by_image_path(todo.image_path, todo.id):
            await delete_image(todo.image_path)
        delete_file_if_exists(todo.attachment_path)
        await self.todo_repo.delete_todo(todo_id)
        await self.todo_repo.commit()
        await self.search_repo.delete_todo(todo_id)

    async def delete_todos(self, *, skip: int, limit: int, start: int, end: int) -> list[int]:
        if (start or end) and (start < 1 or end < 1 or start > end):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect range")

        if not start and not end:
            todos = await self.todo_repo.get_all_todos()
            ids = [todo.id for todo in todos]
            for todo in todos:
                delete_file_if_exists(todo.attachment_path)
            if os.path.exists(settings.IMAGES_DIR):
                for filename in os.listdir(settings.IMAGES_DIR):
                    delete_file_if_exists(os.path.join(settings.IMAGES_DIR, filename))
            await self.todo_repo.delete_all_todos()
            await self.todo_repo.commit()
            for todo_id in ids:
                await self.search_repo.delete_todo(todo_id)
            return ids

        listed_todos = await self.todo_repo.get_todos(limit=limit, skip=skip)
        selected = listed_todos[start - 1:end]
        ids = [todo.id for todo in selected]
        for todo in selected:
            if not await self.todo_repo.get_other_todo_by_image_path(todo.image_path, todo.id):
                await delete_image(todo.image_path)
            delete_file_if_exists(todo.attachment_path)
        await self.todo_repo.delete_todos(ids)
        await self.todo_repo.commit()
        for todo_id in ids:
            await self.search_repo.delete_todo(todo_id)
        return ids

    async def export_all(self, include_id: bool) -> str:
        todos = await self.todo_repo.get_all_todos()
        return export_todos(todos, include_id)

    async def import_from_file(self, upload: UploadFile) -> None:
        filename = upload.filename or f"{generate_random_filename()}.xlsx"
        import_path = os.path.join(settings.IMPORTS_DIR, filename)
        await save_upload_file(upload, import_path)
        imported_rows = import_todos(import_path)

        for row in imported_rows:
            existing = await self.todo_repo.get_todo(row.id) if row.id else None
            if existing:
                await self.todo_repo.update_todo(
                    existing.id,
                    {
                        "title": row.title,
                        "details": row.details,
                        "completed": row.completed,
                        "tag": row.tag,
                        "created_at": row.created_at or existing.created_at,
                        "completed_at": row.completed_at,
                        "source": row.source,
                        "image_path": row.image_path,
                        "image_hash": row.image_hash,
                        "attachment_path": row.attachment_path,
                    },
                )
                await self.todo_repo.commit()
                await self._sync_to_search(await self.get_todo(existing.id))
                continue

            todo = TodoDB(
                id=row.id,
                title=row.title,
                details=row.details,
                completed=row.completed,
                tag=row.tag,
                created_at=row.created_at or datetime.utcnow(),
                completed_at=row.completed_at,
                source=row.source,
                image_path=row.image_path,
                image_hash=row.image_hash,
                attachment_path=row.attachment_path,
            )
            await self.todo_repo.add_todo(todo)
            await self.todo_repo.commit()
            await self._sync_to_search(todo)

    async def import_issues(self, url: str, token: str) -> None:
        todos = get_todos_by_issues(url, token)
        for row in todos:
            todo = TodoDB(
                title=row.title,
                details=row.details,
                completed=row.completed,
                tag=row.tag,
                created_at=row.created_at or datetime.utcnow(),
                completed_at=row.completed_at,
                source=row.source,
            )
            await self.todo_repo.add_todo(todo)
            await self.todo_repo.commit()
            await self._sync_to_search(todo)

    async def shuffle_tags(self) -> None:
        todos = await self.todo_repo.get_all_todos()
        tags = [tag.value for tag in Tags]
        for index, todo in enumerate(todos):
            next_tag = tags[index % len(tags)]
            await self.todo_repo.update_todo(todo.id, {"tag": next_tag})
            await self.todo_repo.commit()
            await self._sync_to_search(await self.get_todo(todo.id))

    async def get_import_logs(self) -> list[str]:
        if not os.path.exists(settings.IMPORTS_DIR):
            return []
        return sorted(os.listdir(settings.IMPORTS_DIR))

    def get_import_log_path(self, filename: str) -> str:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(settings.IMPORTS_DIR, safe_filename)
        if not os.path.exists(file_path):
            return ""
        return file_path

    async def generate_todos_via_script(self, count: int) -> str:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "generate.py"))
        process = await __import__("asyncio").create_subprocess_exec(
            sys.executable,
            script_path,
            str(count),
            stdout=__import__("asyncio").subprocess.PIPE,
            stderr=__import__("asyncio").subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=stderr.decode() or "Generator failed")
        return stdout.decode()
