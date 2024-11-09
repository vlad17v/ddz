#!/bin/bash

COUNT=${1:-20}

echo "Generating $COUNT todos"

for ((i=1; i <= COUNT; i++)); do
    title="Задача ${i}"
    details="Описание задачи ${i}"

    curl -X 'POST' \
      'http://localhost:8000/todo/add/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
            "title": "'"${title}"'",
            "details": "'"${details}"'"
          }'
done