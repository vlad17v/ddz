FROM python:3.12-slim

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY app /code/app
WORKDIR /code/

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
