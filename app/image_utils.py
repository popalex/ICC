import os

import numpy as np
import torch
from PIL import Image as PILImage  # Alias PIL.Image to avoid conflict
from sklearn.cluster import KMeans
from torchvision import models, transforms

from .clip_labeler import label_clusters
from .database import SessionLocal, Image  # Ensure the database model is imported correctly


# Load pre-trained feature extractor (ResNet)
model = models.resnet18(pretrained=True)
model = torch.nn.Sequential(*(list(model.children())[:-1]))  # Remove final FC layer
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

def extract_features(img_path):
    image = PILImage.open(img_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        features = model(tensor)
    return features.squeeze().numpy()

def process_images_and_cluster(img_paths):
    features = []
    for path in img_paths:
        vec = extract_features(path)
        features.append(vec)

    # Auto-adjust number of clusters based on number of images
    n_clusters = min(len(features), 5)  # You can adjust this as needed
    kmeans = KMeans(n_clusters=n_clusters)
    labels = kmeans.fit_predict(features)

    # Create clusters dictionary to group images
    clusters = {}
    for path, label in zip(img_paths, labels):
        filename = os.path.basename(path)
        clusters.setdefault(str(label), []).append(f"/static/{filename}")

    # Update the database with new clusters and labels
    db = SessionLocal()

    for path, label in zip(img_paths, labels):
        filename = os.path.basename(path)
        image = Image(filename=filename, cluster=int(label), label=None)
        db.merge(image)
    db.commit()

    # Label the clusters using CLIP (now the clusters exist in DB)
    label_clusters()

    db.close()

    return clusters

