import numpy as np
import torch
#import torch.nn.functional as F
from torchvision import transforms#models
from PIL import Image
import cv2

from xray_classifier import load_model, CLASS_NAMES

# ===== 1. Preprocessing function for ndarray =====
def preprocess_xray_image(ndarray_img):
    if len(ndarray_img.shape) == 2:
        ndarray_img = np.stack([ndarray_img] * 3, axis=-1)  # Grayscale to RGB
    pil_img = Image.fromarray(np.uint8(ndarray_img)).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet stats
                             std=[0.229, 0.224, 0.225]),
    ])
    return transform(pil_img).unsqueeze(0)  # Shape: (1, 3, 224, 224)


# ===== 2. Grad-CAM Setup =====
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        # Register hooks
        self.target_layer.register_forward_hook(self._save_activation)
        self.target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_tensor, class_idx):
        output = self.model(input_tensor)
        # if class_idx is None:
        #     class_idx = torch.argmax(output)

        self.model.zero_grad()
        output[:, class_idx].backward()

        # Grad-CAM calculation
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
        activations = self.activations.squeeze(0)

        for i in range(activations.shape[0]):
            activations[i, :, :] *= pooled_gradients[i]

        heatmap = torch.mean(activations, dim=0).cpu().numpy()
        heatmap = np.maximum(heatmap, 0)
        heatmap /= heatmap.max()
        return heatmap#, class_idx.item()

# ===== 3. Overlay CAM on Original Image =====
def overlay_heatmap_on_image(heatmap, original_ndarray, alpha=0.4):
    original_resized = cv2.resize(original_ndarray, (224, 224))
    if len(original_resized.shape) == 2:
        original_resized = cv2.cvtColor(original_resized, cv2.COLOR_GRAY2BGR)

    heatmap_resized = cv2.resize(heatmap, (224, 224))
    heatmap_color = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(np.uint8(original_resized), 1 - alpha, heatmap_color, alpha, 0)
    return overlay

# ===== 4. Example Usage =====
def run_gradcam_on_xray(ndarray_img, label):
    input_tensor = preprocess_xray_image(ndarray_img)
    # Load model
    model = load_model()
    # Use last conv block as target layer
    target_layer = model.conv_head  # ✅ this is the final conv block before pooling
    grad_cam = GradCAM(model, target_layer)
    # Get index of label (class name)
    class_idx = CLASS_NAMES.index(label)
    heatmap = grad_cam.generate(input_tensor, class_idx)

    result_img = overlay_heatmap_on_image(heatmap, ndarray_img)
    return result_img
    # plt.imshow(result_img)
    # plt.axis('off')
    # plt.title(f"Predicted class: {class_idx}")
    # plt.show()

# ===== Example call =====
# Assuming you have a DICOM image already read as ndarray:
# import pydicom
# ds = pydicom.dcmread("some_xray.dcm")
# xray_ndarray = ds.pixel_array

# run_gradcam_on_xray(xray_ndarray)
