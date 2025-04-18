from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app import api

from .database import Image, SessionLocal

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(title="Image Clustering Classifier")

app.include_router(api.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    db = SessionLocal()
    results = db.query(Image).all()

    clusters = {}
    labels = {}
    for image in results:
        cluster_id = str(image.cluster)
        clusters.setdefault(cluster_id, []).append(f"/static/{image.filename}")
        labels[cluster_id] = image.label

    db.close()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "clusters": clusters,
        "labels": labels
    })

