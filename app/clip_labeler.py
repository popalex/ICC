import open_clip
import torch
from PIL import Image
from torchvision import transforms
from .database import SessionLocal, Image

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load CLIP model
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
tokenizer = open_clip.get_tokenizer('ViT-B-32')
model.to(device)
model.eval()

# List of possible labels to match against
TEXT_LABELS = [
    "a dog", "a cat", "a beach", "a mountain", "a sunset", "a person", "a car",
    "food", "nature", "a tree", "a group of people", "a building", "a bird", "a flower"
]

@torch.no_grad()
def label_clusters():
    db = SessionLocal()
    clusters = {}

    # Group images by cluster
    images = db.query(Image).all()
    for img in images:
        clusters.setdefault(img.cluster, []).append(img)

    for cluster_id, imgs in clusters.items():
        # Average CLIP embeddings of images in this cluster
        embeddings = []
        for img in imgs:
            image = Image.open(f"app/static/{img.filename}").convert("RGB")
            tensor = preprocess(image).unsqueeze(0).to(device)
            embedding = model.encode_image(tensor)
            embeddings.append(embedding)

        # Average the embeddings
        avg_embedding = torch.stack(embeddings).mean(dim=0)
        avg_embedding /= avg_embedding.norm()

        # Encode the labels
        text_tokens = tokenizer(TEXT_LABELS).to(device)
        text_features = model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        # Cosine similarity to each label
        similarity = (avg_embedding @ text_features.T).squeeze(0)
        best_label_idx = similarity.argmax().item()
        label = TEXT_LABELS[best_label_idx]

        # Save label to DB
        for img in imgs:
            img.label = label
        db.commit()

    db.close()
