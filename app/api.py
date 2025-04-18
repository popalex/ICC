import os
import uuid
from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from .database import Image, SessionLocal
from .image_utils import process_images_and_cluster

router = APIRouter()

UPLOAD_DIR = "app/static"

@router.post("/api/upload/")
async def upload_images(files: List[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_paths = []
    for file in files:
        # Generate a unique filename
        name, ext = os.path.splitext(file.filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        file_paths.append(file_path)

    clusters = process_images_and_cluster(file_paths)

    return JSONResponse(content={"clusters": clusters})


@router.get("/api/clusters/")
def get_clusters():
    db = SessionLocal()
    results = db.query(Image).all()

    clusters = {}
    for image in results:
        clusters.setdefault(str(image.cluster), []).append(f"/static/{image.filename}")

    db.close()
    return {"clusters": clusters}