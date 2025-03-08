# Tahap 1: Build (Menginstall dependencies)
FROM python:3.13-slim AS builder
WORKDIR /app

# Copy file requirements dulu agar cache tetap bisa digunakan
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tahap 2: Runtime (Menjalankan aplikasi tanpa file build yang tidak perlu)
FROM python:3.13-slim
WORKDIR /app

# Copy hanya file yang diperlukan dari tahap build
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
