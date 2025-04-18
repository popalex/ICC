from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

@app.post("/upload/", response_class=HTMLResponse)
async def upload_images(request: Request):
    form = await request.form()
    files = form.getlist("files")

    # Convert files to List[UploadFile]
    # upload_files = [UploadFile(file.filename, file.file, file.content_type) for file in files]

    await api.upload_images(files)

    # Redirect to / page to display clusters
    return RedirectResponse(url="/", status_code=303)
