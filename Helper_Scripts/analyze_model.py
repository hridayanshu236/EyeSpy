import torch
import numpy as np
import cv2
import os
from torchvision import transforms
import sys
from models import (
    ObjectDetectionCNN,
    ObjectDetectionResNet,
    ObjectDetectionDenseNet121,
    ObjectDetectionMobileNetV2
)

def analyze_model_output(model_type="cnn", model_path=None):
    """Analyze a model's output structure and behavior"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Select model
    if model_type == "cnn":
        model = ObjectDetectionCNN(input_channels=3, num_predictions=2).to(device)
    elif model_type == "resnet":
        model = ObjectDetectionResNet(num_predictions=2).to(device)
    elif model_type in ("densenet", "densenet121"):
        model = ObjectDetectionDenseNet121(num_predictions=2).to(device)
    elif model_type in ("mobilenet", "mobilenetv2"):
        model = ObjectDetectionMobileNetV2(num_predictions=2).to(device)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    # Load weights if a path is provided
    if model_path and os.path.exists(model_path):
        try:
            checkpoint = torch.load(model_path, map_location=device)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
                print(f"Loaded weights from {model_path}")
                if 'classes' in checkpoint:
                    print(f"Model detects these classes: {checkpoint['classes']}")
                if 'model_architecture' in checkpoint:
                    print(f"Model architecture: {checkpoint['model_architecture']}")
            else:
                model.load_state_dict(checkpoint)
                print(f"Loaded raw state dict from {model_path}")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return
    else:
        print("Using untrained model (random weights)")

    # Set to evaluation mode
    model.eval()

    # Create a test image (black image)
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)
    # White rectangle (potential "object")
    cv2.rectangle(test_img, (50, 50), (150, 150), (255, 255, 255), -1)

    # Transform the image
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    input_tensor = transform(test_img).unsqueeze(0).to(device)

    # Run inference
    with torch.no_grad():
        output = model(input_tensor)

    # Analyze the output structure
    print("\nModel Output Analysis:")
    print(f"Output shape: {output.shape}")
    print(f"This means the model predicts {output.shape[1]} objects with {output.shape[2]} values each")

    # Check the default prediction values
    print("\nDefault prediction values:")
    for i in range(output.shape[1]):
        confidence = torch.sigmoid(output[0, i, 0]).item()
        box = output[0, i, 1:5].detach().cpu().numpy()
        print(f"Object {i+1}: Confidence={confidence:.4f}, Box={box}")

    return model

if __name__ == "__main__":
    import glob

    # Allow command-line arguments: python analyze_model_output.py [cnn|resnet|densenet|mobilenet] [model_path]
    if len(sys.argv) >= 3:
        model_type = sys.argv[1].lower()
        model_path = sys.argv[2]
    else:
        model_files = []
        search_paths = ["*.pth", "models/*.pth", "saved_models/*.pth","Trained_Models/*.pth"]
        for path in search_paths:
            model_files.extend(glob.glob(path))
        if model_files:
            print(f"Found these model files: {model_files}")
            fname = os.path.basename(model_files[0]).lower()
            if "resnet" in fname:
                model_type = "resnet"
            elif "densenet" in fname:
                model_type = "densenet"
            elif "mobilenet" in fname:
                model_type = "mobilenet"
            else:
                model_type = "cnn"
            model_path = model_files[0]
        else:
            print("No model files found. Will use untrained model.")
            model_type = "cnn"
            model_path = None

    # Analyze the model
    analyze_model_output(model_type, model_path)