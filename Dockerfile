FROM        python:3.10

ENV         PYTHONUNBUFFERED=1

WORKDIR     /home

COPY        . .

RUN         ls -la

RUN         pip install -r requirements.txt \
            && adduser --disabled-password --no-create-home doe

EXPOSE      8000

CMD         ["uvicorn", "main:app", "--port", "8000", "--host", "0.0.0.0"]

