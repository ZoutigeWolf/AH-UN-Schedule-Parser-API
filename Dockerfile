FROM python:3.11-alpine

COPY requirements.txt ./

RUN apk update && apk add
RUN apk add --update alpine-sdk

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:80", "-w", "4", "server:app"]
