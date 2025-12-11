import os
import argparse

def validate_yolo_label_line(line, num_classes=None):
    parts = line.strip().split()
    if len(parts) != 5:
        return False, f"Expected 5 elements, got {len(parts)}"
    try:
        class_id, x, y, w, h = parts
        class_id = int(class_id)
        x, y, w, h = map(float, (x, y, w, h))
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
            return False, f"Coordinates out of [0,1]: {x}, {y}, {w}, {h}"
        if w <= 0 or h <= 0:
            return False, f"Width/height must be positive: w={w}, h={h}"
        if num_classes is not None and not (0 <= class_id < num_classes):
            return False, f"Class index out of range: {class_id}"
    except Exception as e:
        return False, f"Non-numeric value: {e}"
    return True, ""

def validate_yolo_labels(label_dir, num_classes=None):
    invalid_files = []
    for fname in os.listdir(label_dir):
        if not fname.endswith('.txt'):
            continue
        path = os.path.join(label_dir, fname)
        with open(path, 'r') as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                valid, error = validate_yolo_label_line(line, num_classes=num_classes)
                if not valid:
                    invalid_files.append((fname, idx, error, line))
    return invalid_files

def check_images_and_labels(image_dir, label_dir, valid_extensions=None):
    """
    Checks if every image in image_dir has a corresponding valid label in label_dir.
    Returns:
        images_missing_labels: list of image files without a corresponding label file
        labels_missing_images: list of label files without a corresponding image file
        images_with_empty_labels: list of image files whose label file is empty
    """
    if valid_extensions is None:
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')

    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(valid_extensions)]
    label_files = [f for f in os.listdir(label_dir) if f.endswith('.txt')]

    image_basenames = set(os.path.splitext(f)[0] for f in image_files)
    label_basenames = set(os.path.splitext(f)[0] for f in label_files)

    images_missing_labels = sorted([f for f in image_files if os.path.splitext(f)[0] not in label_basenames])
    labels_missing_images = sorted([f for f in label_files if os.path.splitext(f)[0] not in image_basenames])

    images_with_empty_labels = []
    for f in image_files:
        base = os.path.splitext(f)[0]
        label_path = os.path.join(label_dir, base + ".txt")
        if os.path.isfile(label_path):
            with open(label_path, "r") as lf:
                contents = lf.read().strip()
                if not contents:
                    images_with_empty_labels.append(f)

    return images_missing_labels, labels_missing_images, images_with_empty_labels

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate YOLO label files and check correspondence with images.")
    parser.add_argument("image_dir", help="Path to directory containing image files")
    parser.add_argument("label_dir", help="Path to directory containing YOLO .txt label files")
    parser.add_argument("num_classes", type=int, nargs='?', default=None, help="Maximum number of classes (optional)")
    args = parser.parse_args()

    # 1. Check image-label correspondence
    images_missing_labels, labels_missing_images, images_with_empty_labels = check_images_and_labels(
        args.image_dir, args.label_dir
    )

    if images_missing_labels:
        print("Images missing label files:")
        for f in images_missing_labels:
            print("  ", f)
    else:
        print("All images have corresponding label files.")

    if labels_missing_images:
        print("Label files missing corresponding images:")
        for f in labels_missing_images:
            print("  ", f)
    else:
        print("All label files have corresponding images.")

    if images_with_empty_labels:
        print("Images whose label files are empty (no objects):")
        for f in images_with_empty_labels:
            print("  ", f)
    else:
        print("No empty label files found.")

    # 2. Validate label file contents
    results = validate_yolo_labels(args.label_dir, num_classes=args.num_classes)
    if results:
        print("\nInvalid YOLO label lines found:")
        for fname, idx, error, line in results:
            print(f"File: {fname}, Line: {idx}, Error: {error}\n    > {line}")
    else:
        print("\nAll label file contents are valid!")