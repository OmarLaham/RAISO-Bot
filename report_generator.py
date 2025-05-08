# Model used: R2Gen trained on dataset: IU X-Ray
# Model GitHub link: https://github.com/cuhksz-nlp/R2Gen


from PIL import Image
import numpy as np
import torchvision.transforms as transforms

def preprocess_image(image_array):
    # Convert NumPy array to PIL Image
    image = Image.fromarray(image_array).convert('RGB')
    
    # Define the preprocessing transformations
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    
    # Apply transformations
    image = transform(image)
    image = image.unsqueeze(0)  # Add batch dimension
    return image


