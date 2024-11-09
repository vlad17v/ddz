# fastapi-todo-lr1

## Запуск

### Без docker

```bash
# установка с прокси и без
pip install --user --proxy http://login:pass@192.168.232.1:3128 -r requirements.txt
pip install --user -r requirements.txt

uvicorn app.main:app --reload

# генерация туду (по умолчанию 20)
./scripts/generate.sh

# генерация 5 туду
./scripts/generate.sh 5
```

### С docker

```bash
sudo docker build -t 2022-3-03-vor-lr1:v1 .

# для генерации туду
sudo docker build -t 2022-3-03-vor-lr1-generate -f Dockerfile_generate .
```

#### Для пользователя

```bash
sudo docker run --rm -p 8000:8000 --name app 2022-3-03-vor-lr1:v1

# with database save
sudo docker run --rm -p 8000:8000 --name app -v "${PWD}/data/":/code/data/ 2022-3-03-vor-lr1:v1
```

#### Для разработчика

```bash
sudo docker run --rm -p 8000:8000 --name app -v "${PWD}/app":/code/app -v "${PWD}/data/":/code/data/ 2022-3-03-vor-lr1:v1

# генерация туду
sudo docker run --rm --network=host 2022-3-03-vor-lr1-generate 
```
