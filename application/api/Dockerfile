# 1. Official lightweight Python image use kora
FROM python:3.10-slim

# 2. Container er vitor working directory set kora
WORKDIR /app

# 3. Prothome dependencies file copy kora ar install kora (Caching optimization er jonno)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Baki API source code guli container-e copy kora
COPY . .

# 5. FastAPI application je port-e run korbe seta expose kora
EXPOSE 8000

# 6. Container start hole Uvicorn server chalu korar command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]