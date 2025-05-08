import os
from glob import glob
import json

import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoTokenizer
from timm import create_model

# Load vision encoder (ViT-base used in MedCLIP)
vision_model = create_model('vit_base_patch16_224', pretrained=True, num_classes=0)
vision_model.eval()

# Preprocessing for MedCLIP (224x224, normalization)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],  # ImageNet
        std=[0.229, 0.224, 0.225]
    )
])

def embed_xray(image_path):
    image = Image.open(image_path).convert('RGB')
    tensor = transform(image).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        embedding = vision_model(tensor).squeeze().numpy()
    return embedding
    
    

image_paths = glob('path_to_xrays/*.png')  # or .jpg, .jpeg
records = []

for path in image_paths:
    vec = embed_xray(path)
    records.append({
        "filename": os.path.basename(path),
        "embedding": vec.tolist()
    })

# Save for Azure AI Search ingestion
with open("medclip_xray_vectors.jsonl", "w") as f:
    for record in records:
        json.dump(record, f)
        f.write("\n")
