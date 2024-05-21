FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN --mount=type=secret,id=DB_URL \
  --mount=type=secret,id=DB_USER \
  --mount=type=secret,id=DB_PASSWORD \
   export DB_URL=$(cat /run/secrets/DB_URL) && \
   export DB_USER=$(cat /run/secrets/DB_USER) && \
   export DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]