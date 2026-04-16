FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot file
COPY main.py .

# Railway بيستخدم PORT environment variable
ENV PORT=8080

# تشغيل البوت
CMD ["python", "main.py"]
