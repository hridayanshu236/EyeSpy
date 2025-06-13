import torch
import cv2
import numpy as np
import os
from torchvision import transforms

# Define your model architecture (same as in camera_widget.py)
class ObjectDetectionCNN(torch.nn.Module):
    def __init__(self, input_channels=3, num_predictions=2):
        super(ObjectDetectionCNN, self).__init__()

        def conv_block(in_channels, out_channels, num_convs, pool=True):
            layers = []
            for _ in range(num_convs):
                layers.append(torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1))
                layers.append(torch.nn.ReLU(inplace=True))
                in_channels = out_channels
            if pool:
                layers.append(torch.nn.MaxPool2d(kernel_size=2, stride=2))
            return torch.nn.Sequential(*layers)

        self.features = torch.nn.Sequential(
            conv_block(input_channels, 64, num_convs=2),
            conv_block(64, 128, num_convs=2),
            conv_block(128, 256, num_convs=4),
            conv_block(256, 512, num_convs=4),
            conv_block(512, 512, num_convs=4),
        )

        self.adapt_pool = torch.nn.AdaptiveAvgPool2d((7, 7))
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(512 * 7 * 7, 4096),
            torch.nn.ReLU(inplace=True),
            torch.nn.Linear(4096, 4096),
            torch.nn.ReLU(inplace=True),
            torch.nn.Linear(4096, num_predictions * 5)
        )
        self.num_predictions = num_predictions

    def forward(self, x):
        x = self.features(x)
        x = self.adapt_pool(x)
        x = self.classifier(x)
        x = x.view(x.shape[0], self.num_predictions, 5)
        return x

def analyze_model_output(model_path=None):
    """Analyze a model's output structure and behavior"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create a model instance
    model = ObjectDetectionCNN(input_channels=3, num_predictions=2).to(device)
    
    # Load weights if a path is provided
    if model_path and os.path.exists(model_path):
        try:
            checkpoint = torch.load(model_path, map_location=device)
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
                print(f"Loaded weights from {model_path}")
                
                # Check if there's information about what the model detects
                if 'classes' in checkpoint:
                    print(f"Model detects these classes: {checkpoint['classes']}")
                elif 'model_architecture' in checkpoint:
                    print(f"Model architecture: {checkpoint['model_architecture']}")
            else:
                print(f"Model file doesn't contain expected 'model_state_dict'")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
    else:
        print("Using untrained model (same as your current setup)")
    
    # Set to evaluation mode
    model.eval()
    
    # Create a test image (black image)
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)
    
    # Add some visual elements that might trigger detection
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
        box = output[0, i, 1:5].cpu().numpy()
        print(f"Object {i+1}: Confidence={confidence:.4f}, Box={box}")
    
    # If the model predicts a consistent score around 0.5 for an untrained model,
    # that suggests the initial bias is near 0, which gives 0.5 after sigmoid
    
    return model

if __name__ == "__main__":
    # Search for model files in common locations
    model_files = []
    search_paths = ["*.pth", "models/*.pth", "saved_models/*.pth"]
    
    for path in search_paths:
        import glob
        model_files.extend(glob.glob(path))
    
    if model_files:
        print(f"Found these model files: {model_files}")
        model_path = model_files[0]  # Use the first one found
    else:
        print("No model files found. Will use untrained model.")
        model_path = None
    
    # Analyze the model
    analyze_model_output(model_path)
    
    print("\nProblem diagnosis:")
    print("1. The consistent 0.50295806 score suggests your system is using an untrained model")
    print("2. An untrained model initialized with common techniques will often output")
    print("   values near 0, which becomes ~0.5 after sigmoid activation")
    print("3. This is causing false detections because your threshold is also 0.5")
    
    print("\nRecommendations:")
    print("1. Increase the confidence threshold to 0.7 or higher to avoid false positives")
    print("2. Verify your model file's location and format using the find_model.py script")
    print("3. If your model file can't be found, try manually copying it to the model/ directory")
    print("4. Update the model paths in your code to the exact location where your model is stored")