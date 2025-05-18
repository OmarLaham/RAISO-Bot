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

def embed_xray(img: Image):
    tensor = transform(img).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        embedding = vision_model(tensor).squeeze().numpy()
    return embedding.tolist()  # Convert NumPy array to list
