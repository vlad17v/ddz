from datetime import datetime
from urllib.parse import urlparse

import gitlab
from fastapi import HTTPException
from loguru import logger

from app.models.schemas import TodoExportRow
from app.models.schemas import TodoSource


def parse_link(full_link: str) -> tuple[str, str] | None:
    result = urlparse(full_link)
    if all([result.scheme, result.netloc, result.path]):
        split_link = full_link.split("/", 3)
        return split_link[0] + "//" + split_link[2], split_link[3]
    return None


def import_issues(full_link: str, access_token: str):
    parsed_link = parse_link(full_link)
    if parsed_link is None:
        return None

    server_part, project_part = parsed_link
    try:
        git = gitlab.Gitlab(url=server_part, private_token=access_token)
        git.auth()
    except Exception as err:
        logger.warning(f"Trying to skip ssl: {err}")
        git = gitlab.Gitlab(url=server_part, private_token=access_token, ssl_verify=False)
        git.auth()
    project = git.projects.get(project_part)
    return project.issues.list(all=True)


def get_todos_by_issues(full_link: str, access_token: str) -> list[TodoExportRow]:
    issues = import_issues(full_link, access_token)
    if issues is None:
        raise HTTPException(status_code=444, detail="Failed to import issues: Invalid link or authentication error.")

    todos: list[TodoExportRow] = []
    for issue in issues:
        todos.append(
            TodoExportRow(
                title=issue.title,
                details=issue.description or "",
                completed=issue.state == "closed",
                created_at=datetime.fromisoformat(issue.created_at.replace("Z", "+00:00")),
                completed_at=datetime.fromisoformat(issue.due_date.replace("Z", "+00:00"))
                if issue.due_date and issue.state == "closed"
                else None,
                source=TodoSource.imported.value,
            )
        )
    return todos
