FROM python:3.11-alpine

WORKDIR /app

RUN apk update

RUN pip install --upgrade pip
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--port", "8000", "--reload", "--host", "0.0.0.0"]
