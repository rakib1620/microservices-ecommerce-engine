# 1. Official lightweight Python image
FROM python:3.10-slim

# 2. Working directory set kora
WORKDIR /app

# 3. Dependencies install kora
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Worker source code copy kora
COPY . .

# 5. Worker run korar command
CMD ["python", "worker.py"]