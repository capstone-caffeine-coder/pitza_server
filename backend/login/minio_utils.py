
from minio import Minio
import os
from django.conf import settings


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", getattr(settings, 'MINIO_ENDPOINT', 'localhost:9000'))
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin'))
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin'))
MINIO_SECURE = os.getenv("MINIO_SECURE", str(getattr(settings, 'MINIO_SECURE', False))).lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", getattr(settings, 'MINIO_BUCKET_NAME', 'profile-pictures'))

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)


try:
    if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
        minio_client.make_bucket(MINIO_BUCKET_NAME)
        print(f"MinIO bucket '{MINIO_BUCKET_NAME}' created.")
except Exception as e:
    print(f"Error checking/creating MinIO bucket '{MINIO_BUCKET_NAME}': {e}")