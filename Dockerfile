FROM python:3.11-slim

RUN useradd -m -r gatewayuser
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN chown -R gatewayuser:gatewayuser /usr/src/app
USER gatewayuser

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
