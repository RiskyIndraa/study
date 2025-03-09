# Tahap 1: Build (Menginstall dependencies)
FROM python:3.13-slim AS builder
WORKDIR /app

# Copy file requirements dulu agar cache tetap bisa digunakan
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Tahap 2: Runtime (Menjalankan aplikasi tanpa file build yang tidak perlu)
FROM python:3.13-slim
WORKDIR /app

# Copy aplikasi dan dependencies yang diperlukan
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Pastikan gunicorn tersedia
RUN pip install gunicorn

# Gunicorn menjalankan Flask di port 5000
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
