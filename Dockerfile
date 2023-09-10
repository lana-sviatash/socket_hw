FROM python:3.10

WORKDIR $APP_HOME

RUN pip install poetry

COPY . .

RUN poetry install

EXPOSE 4000

ENTRYPOINT ["poetry", "run", "python", "hw_socket/main.py"]