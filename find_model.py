import os
import torch
from glob import glob

def find_model_files():
    """Search for model files in common directories"""
    search_patterns = [
        "*.pth",
        "models/*.pth",
        "saved_modelss/*.pth",
        "../*.pth",
        "../models/*.pth",
        "../saved_models/*.pth"
    ]
    
    found_files = []
    for pattern in search_patterns:
        matches = glob(pattern)
        for match in matches:
            found_files.append(os.path.abspath(match))
    
    return found_files

def check_model_file(filepath):
    """Check if a file is a valid model checkpoint"""
    try:
        checkpoint = torch.load(filepath, map_location="cpu")
        print(f"\nFile: {filepath}")
        
        if isinstance(checkpoint, dict):
            print(f"Type: Checkpoint dictionary with {len(checkpoint)} keys")
            print(f"Keys: {list(checkpoint.keys())}")
            
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
                print(f"Model state dict contains {len(state_dict)} parameters")
                print("Sample keys:", list(state_dict.keys())[:3])
                
                if 'epoch' in checkpoint:
                    print(f"Trained for {checkpoint['epoch']} epochs")
                
                if 'model_architecture' in checkpoint:
                    print(f"Architecture: {checkpoint['model_architecture']}")
                
                return True
        elif isinstance(checkpoint, torch.nn.Module):
            print("Type: Direct model instance")
            return True
        else:
            print(f"Type: Unknown format - {type(checkpoint)}")
            return False
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        return False

if __name__ == "__main__":
    print("Searching for model files...")
    model_files = find_model_files()
    
    if not model_files:
        print("No model files found in the search paths.")
        print("Please ensure your model file is in one of these locations with .pth extension:")
        print("- Current directory")
        print("- model/ subdirectory")
        print("- saved_models/ subdirectory")
    else:
        print(f"Found {len(model_files)} potential model files:")
        for i, filepath in enumerate(model_files, 1):
            print(f"{i}. {filepath}")
        
        print("\nChecking model files...")
        valid_models = []
        for filepath in model_files:
            if check_model_file(filepath):
                valid_models.append(filepath)
        
        if valid_models:
            print(f"\nFound {len(valid_models)} valid model checkpoints.")
            print("You can use any of these paths in your camera_widget.py")
        else:
            print("\nNo valid model checkpoints found.")
            print("Please ensure your model file has the expected format with 'model_state_dict'.")