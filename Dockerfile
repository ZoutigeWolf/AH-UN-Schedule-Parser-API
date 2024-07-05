FROM python:latest

COPY requirements.txt ./

RUN apt-get update && apt-get upgrade
RUN apt-get install build-essential

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:80", "-w", "4", "server:app"]
