FROM python:3.11

WORKDIR /home/ChatApp

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
