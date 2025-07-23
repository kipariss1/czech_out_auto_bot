FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["sh", "-c", "python run_bot.py & cd web_app && uvicorn main:app --host 0.0.0.0 --port 8000"]