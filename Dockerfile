FROM python:3.11-alpine

COPY requirements.txt ./

RUN apt-get install build-essential
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:80", "-w", "4", "server:app"]
