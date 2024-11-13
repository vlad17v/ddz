FROM python:3.12-slim

RUN apt-get update && apt-get install curl -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY scripts /code/scripts
COPY app /code/app
WORKDIR /code/

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

