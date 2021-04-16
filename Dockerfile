FROM python:3.9.1-alpine3.12

RUN apk update
RUN apk add bash
RUN apk add vim

WORKDIR /app

COPY ./BotCreds.py .
COPY ./requirements.txt .
COPY ./SuicidalWatchBot.py .

RUN pip install -r requirements.txt

CMD ["python", "./SuicidalWatchBot.py"]