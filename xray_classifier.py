import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
import timm


# Define CheXpert or ChestX-ray14 labels (example)
CLASS_NAMES = [
    'Atelectasis', 'Cardiomegaly', 'Consolidation', 'Edema', 'Effusion',
    'Emphysema', 'Fibrosis', 'Hernia', 'Infiltration', 'Mass',
    'Nodule', 'Pleural_Thickening', 'Pneumonia', 'Pneumothorax'
]

model_checkpoint_path = None # 'path_to_your_trained_model.pth'

# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # EfficientNetB0 size
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],  # Imagenet mean
                         [0.229, 0.224, 0.225])  # Imagenet std
])

# Load EfficientNet B0 model from timm
def load_model(num_classes=len(CLASS_NAMES), checkpoint_path=None):
    model = timm.create_model('efficientnet_b0', pretrained=True)
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.classifier.in_features, num_classes)
    )
    if checkpoint_path:
        model.load_state_dict(torch.load(checkpoint_path, map_location='cpu'))
    model.eval()
    return model

# Inference function
def classify_xray(image: Image.Image):#, model: torch.nn.Module
    # Convert DICOM pixel ndarray to PIL Image
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    elif not isinstance(image, Image.Image):
        raise ValueError("Input must be a PIL Image or a NumPy array.")
    # Preprocess image
    if image.mode != 'RGB':
        image = image.convert('RGB')
    input_tensor = transform(image).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        # Load model (use your own checkpoint if available)
        model = load_model(checkpoint_path=model_checkpoint_path)
        outputs = model(input_tensor)
        probs = torch.sigmoid(outputs).squeeze().numpy()  # multi-label sigmoid
    results = {
        label: float(prob) for label, prob in zip(CLASS_NAMES, probs)
    }
    return results