FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["hypercorn", "app:app", "-b", "0.0.0.0:5000"]
