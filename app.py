from flask import Flask, request, render_template, redirect, url_for, jsonify
import boto3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# AWS Configuration (Using environment variables)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
API_URL = os.getenv("API_GATEWAY_URL")

# Validasi API_URL agar tidak None
if not API_URL:
    raise ValueError("❌ ERROR: API_GATEWAY_URL is not set! Please check your environment variables.")

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION,
)

@app.route("/")
def index():
    try:
        response = requests.get(API_URL)
        users = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch data from API: {str(e)}"}), 500

    return render_template("index.html", users=users, s3_bucket=f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/")

@app.route("/users", methods=["POST"])
def add_user():
    name = request.form["name"]
    email = request.form["email"]
    institution = request.form["institution"]
    position = request.form["position"]
    phone = request.form["phone"]
    image = request.files["image"]

    # 1️⃣ Cek apakah email sudah ada di database
    check_response = requests.get(f"{API_URL}?email={email}")

    if check_response.status_code == 409:  # Jika email sudah ada
        return jsonify({"error": "Email already exists"}), 409

    # 2️⃣ Jika email belum ada, lanjut upload gambar
    image_url = ""
    if image:
        image_filename = f"users/{image.filename}"
        try:
            s3_client.upload_fileobj(image, S3_BUCKET, image_filename)
            image_url = f"https://{S3_BUCKET}.s3-{AWS_REGION}.amazonaws.com/{image_filename}"
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # 3️⃣ Simpan user ke database
    user_data = {
        "name": name,
        "email": email,
        "institution": institution,
        "position": position,
        "phone": phone,
        "image_url": image_url,
    }

    response = requests.post(API_URL, json=user_data)

    if response.status_code == 409:
        return jsonify({"error": "Email already exists"}), 409

    return redirect(url_for("index"))

@app.route("/users/<int:user_id>/delete", methods=["DELETE"])
def delete_user(user_id):
    response = requests.delete(f"{API_URL}/{user_id}")
    
    if response.status_code == 204:
        return jsonify({"message": "User deleted successfully"}), 200

    try:
        return jsonify(response.json()), response.status_code
    except requests.exceptions.JSONDecodeError:
        return jsonify({"error": "Unexpected empty response"}), response.status_code

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    response = requests.get(f"{API_URL}/{user_id}")
    return jsonify(response.json()), response.status_code

@app.route("/users/<int:user_id>", methods=["PUT", "PATCH"])
def update_user(user_id):
    data = request.json
    response = requests.put(f"{API_URL}/{user_id}", json=data)

    if response.status_code == 200:
        return jsonify({"message": "User updated successfully", "data": response.json()})
    else:
        return jsonify({"error": "Failed to update user"}), response.status_code

# Jalankan hanya saat di mode development (Mencegah bentrok dengan Gunicorn di AWS)
if __name__ == "__main__":
    if os.getenv("FLASK_ENV") == "development":
        app.run(host="0.0.0.0", port=5000, debug=True)
