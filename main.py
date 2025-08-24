import os
import requests
from google.cloud import storage
from datetime import datetime
from PIL import Image
from io import BytesIO

# --- 設定項目 ---
# 環境変数として設定するため、コードには直接書かない
# HF_API_TOKEN = os.environ.get("HUGGING_FACE_API_KEY")
# GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")

IMAGE_PROMPT = "a beautiful anime girl, intricate details, highly detailed, fantasy style"
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

def generate_image(prompt):
    """Hugging Face AIモデルで画像を生成する関数"""
    headers = {"Authorization": f"Bearer {os.environ.get('HUGGING_FACE_API_KEY')}"}
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.content
    else:
        print(f"画像生成に失敗しました: {response.status_code}, {response.text}")
        return None

def upload_to_gcs(image_bytes, bucket_name, destination_blob_name):
    """生成した画像をGoogle Cloud Storageにアップロードする関数"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
        return blob.public_url
    except Exception as e:
        print(f"GCSへのアップロード中にエラーが発生しました: {e}")
        return None

def run_generator(request):
    """GCFの実行トリガーとなるメイン関数"""
    print("画像生成を開始します...")
    image_data = generate_image(IMAGE_PROMPT)
    
    if image_data:
        image = Image.open(BytesIO(image_data))
        jpeg_data = BytesIO()
        image.save(jpeg_data, format="JPEG")
        jpeg_data.seek(0)
        
        filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        bucket_name = os.environ.get("GCS_BUCKET_NAME")
        
        print(f"{filename} をGCSにアップロードします...")
        public_url = upload_to_gcs(jpeg_data.getvalue(), bucket_name, filename)
        
        if public_url:
            print("画像のアップロードが成功しました。")
    else:
        print("画像の生成に失敗しました。")

    return "OK", 200