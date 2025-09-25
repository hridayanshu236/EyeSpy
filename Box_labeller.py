import os
import cv2
import numpy as np
from pathlib import Path

def read_yolo_labels(label_file):
    """
    Read YOLO format labels from a text file.
    
    Args:
        label_file (str): Path to the label file
        
    Returns:
        list: List of tuples containing (class_id, center_x, center_y, width, height)
    """
    labels = []
    if os.path.exists(label_file):
        with open(label_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        labels.append((class_id, center_x, center_y, width, height))
    return labels

def yolo_to_pixel_coords(center_x, center_y, width, height, img_width, img_height):
    """
    Convert YOLO normalized coordinates to pixel coordinates.
    
    Args:
        center_x, center_y, width, height: YOLO normalized coordinates (0-1)
        img_width, img_height: Image dimensions in pixels
        
    Returns:
        tuple: (x1, y1, x2, y2) pixel coordinates for bounding box
    """
    # Convert center coordinates to pixel values
    center_x_px = center_x * img_width
    center_y_px = center_y * img_height
    
    # Convert width and height to pixel values
    width_px = width * img_width
    height_px = height * img_height
    
    # Calculate top-left and bottom-right coordinates
    x1 = int(center_x_px - width_px / 2)
    y1 = int(center_y_px - height_px / 2)
    x2 = int(center_x_px + width_px / 2)
    y2 = int(center_y_px + height_px / 2)
    
    return x1, y1, x2, y2

def draw_bounding_boxes(image_path, label_path, output_dir, class_names=None):
    """
    Draw bounding boxes on an image based on YOLO labels.
    
    Args:
        image_path (str): Path to the input image
        label_path (str): Path to the corresponding label file
        output_dir (str): Directory to save the output image
        class_names (dict): Optional dictionary mapping class IDs to names
    """
    # Read the image
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image: {image_path}")
        return
    
    img_height, img_width = image.shape[:2]
    
    # Read YOLO labels
    labels = read_yolo_labels(label_path)
    
    if not labels:
        print(f"No labels found in: {label_path}")
        return
    
    # Draw bounding boxes
    for class_id, center_x, center_y, width, height in labels:
        # Convert to pixel coordinates
        x1, y1, x2, y2 = yolo_to_pixel_coords(center_x, center_y, width, height, img_width, img_height)
        
        # Draw green bold bounding box
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)  # Green color, thickness 3
        
        # Add class label
        if class_names and class_id in class_names:
            label_text = class_names[class_id]
        else:
            label_text = f"Class {class_id}"
        
        # Put text above the bounding box
        label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), (0, 255, 0), -1)
        cv2.putText(image, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Save the image with drawn bounding boxes
    output_path = os.path.join(output_dir, os.path.basename(image_path))
    cv2.imwrite(output_path, image)
    print(f"Saved image with bounding boxes: {output_path}")

def process_dataset(image_dir, label_dir, output_dir="Drawn BBox Data", class_names=None):
    """
    Process all images and their corresponding label files from separate directories.
    
    Args:
        image_dir (str): Directory containing image files
        label_dir (str): Directory containing label files
        output_dir (str): Directory to save images with drawn bounding boxes
        class_names (dict): Optional dictionary mapping class IDs to names
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(Path(image_dir).glob(f"*{ext}"))
        image_files.extend(Path(image_dir).glob(f"*{ext.upper()}"))
    
    if not image_files:
        print(f"No image files found in {image_dir}")
        return
    
    processed_count = 0
    
    for image_path in image_files:
        # Generate corresponding label file path in the label directory
        image_name = image_path.stem  # Get filename without extension
        label_path = Path(label_dir) / f"{image_name}.txt"
        
        if label_path.exists():
            draw_bounding_boxes(str(image_path), str(label_path), output_dir, class_names)
            processed_count += 1
        else:
            print(f"Label file not found for: {image_path} (expected: {label_path})")
    
    print(f"\nProcessing complete! {processed_count} images processed.")
    print(f"Output saved to: {output_dir}")

def main():
    """
   
    """
  
    image_directory = "./Image_augmented"      
    label_directory = "./Label_augmented"     
    output_directory = "Drawn BBox Data"
    
    # Optional: Define class names (customize based on your dataset)
    class_names = {
        0: "Class_0",
        1: "Class_1"
    }
    
    print("YOLO Bounding Box Drawer")
    print("=" * 30)
    print(f"Image directory: {image_directory}")
    print(f"Label directory: {label_directory}")
    print(f"Output directory: {output_directory}")
    print()
    
    # Check if directories exist
    if not os.path.exists(image_directory):
        print(f"Error: Image directory '{image_directory}' not found!")
        return
    
    if not os.path.exists(label_directory):
        print(f"Error: Label directory '{label_directory}' not found!")
        return
    
    # Process the dataset
    process_dataset(image_directory, label_directory, output_directory, class_names)

if __name__ == "__main__":
    main()

