import os
from os import path
from glob import glob
import json

import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoTokenizer
from timm import create_model

import pandas as pd
import numpy as np

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
    

# Store embedding records to write to one document later for Azure AI Search ingestion
records = []
images_dir = path.join("XRay-Chest-NIH-Random-dataset", "as_png")

# Load sample labels file to label each file record
df_labels = pd.read_csv(path.join("XRay-Chest-NIH-Random-dataset", "sample_lables_minimized.csv"))

image_paths = glob(f'{images_dir}/*.png')  # or .jpg, .jpeg

iterator = 1
for img_path in image_paths:

    print(f"> Embedding:", str(img_path))
    filename = os.path.basename(img_path)
    labels = df_labels.query("`Image Index`==@filename").iloc[0]['Finding Labels']
    labels = labels.split("|") if "|" in labels else [labels] # convert to list
    vec = embed_xray(img_path)
    records.append({
        "id": str(iterator),
        "filename": os.path.basename(img_path),
        "labels": labels,
        "embedding": vec.tolist()
    })
    
    iterator += 1
    
print("> Created records in RAM..")
print("> Writing records to .jsonl file for Azure AI Search ingestion..")


# Save for Azure AI Search ingestion
with open("medclip_xray_vectors.jsonl", "w") as f:
    for record in records:
        json.dump(record, f)
        f.write("\n")
        
print(".JSONL file crearted for Azure AI Search ingestion")
print("======================================")

print("\nDone!")
