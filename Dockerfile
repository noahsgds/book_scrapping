FROM python:3.11-slim

# Empêche Python de bufferiser les sorties standard
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y cron

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ /app/src/

COPY crontab.sh /etc/cron.d/data-pipeline-cron
RUN chmod 0644 /etc/cron.d/data-pipeline-cron
RUN crontab /etc/cron.d/data-pipeline-cron

CMD ["cron", "-f"]