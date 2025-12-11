import os
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2

class YOLOAugmenter:
    def __init__(self):
        """Optimized augmentation pipeline for speed with lighter transformations"""
        self.target_size = (640, 640)
        self.transform = A.Compose([
            # Spatial transforms (faster ones)
            A.HorizontalFlip(p=0.7),
            A.RandomRotate90(p=0.4),
            A.ShiftScaleRotate(
                shift_limit=0.15,
                scale_limit=0.3,
                rotate_limit=10,  # Lower rotation limit for faster performance
                p=0.5,
                border_mode=cv2.BORDER_REFLECT
            ),
            # Geometric transforms (with less distortion)
            A.OneOf([
                A.ElasticTransform(alpha=10, sigma=5, alpha_affine=5, p=0.2),
                A.GridDistortion(num_steps=3, distort_limit=0.05, p=0.2),
            ], p=0.3),
            # Color transforms
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=15, p=0.6),
            A.CLAHE(clip_limit=3.0, p=0.4),
            # Noise
            A.OneOf([
                A.GaussNoise(var_limit=(10.0, 30.0), p=0.3),  # Less noise intensity for faster processing
                A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.4), p=0.3),
            ], p=0.4),
            # Final resize (ensure always 640x640)
            A.Resize(self.target_size[0], self.target_size[1], interpolation=cv2.INTER_LINEAR)
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels'], min_visibility=0.7, min_area=100))

    def augment_image(self, image, bboxes, class_labels):
        return self.transform(image=image, bboxes=bboxes, class_labels=class_labels)

def load_yolo_label(label_path):
    boxes = []
    class_labels = []
    if not os.path.exists(label_path):
        return boxes, class_labels

    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls, x, y, w, h = map(float, parts)
            boxes.append([x, y, w, h])
            class_labels.append(int(cls))
    return boxes, class_labels

def save_yolo_label(path, boxes, class_labels):
    with open(path, 'w') as f:
        for bbox, cls in zip(boxes, class_labels):
            x, y, w, h = bbox
            f.write(f"{int(cls)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")


def augment_directory(input_img_dir, input_label_dir, output_img_dir, output_label_dir, n_augments=1):
    os.makedirs(output_img_dir, exist_ok=True)
    os.makedirs(output_label_dir, exist_ok=True)

    augmenter = YOLOAugmenter()
    img_files = [f for f in os.listdir(input_img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    for img_file in img_files:
        base_name = os.path.splitext(img_file)[0]
        img_path = os.path.join(input_img_dir, img_file)
        label_path = os.path.join(input_label_dir, f"{base_name}.txt")

        image = cv2.imread(img_path)
        if image is None:
            print(f"Failed to load: {img_path}")
            continue

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w = image.shape[:2]

        bboxes, class_labels = load_yolo_label(label_path)
        if not bboxes:
            continue

        for i in range(n_augments):
            augmented = augmenter.augment_image(image, bboxes, class_labels)
            aug_img = cv2.cvtColor(augmented["image"], cv2.COLOR_RGB2BGR)

            new_img_name = f"{base_name}_aug_{i}.jpg"
            new_lbl_name = f"{base_name}_aug_{i}.txt"

            cv2.imwrite(os.path.join(output_img_dir, new_img_name), aug_img)
            save_yolo_label(os.path.join(output_label_dir, new_lbl_name),
                            augmented['bboxes'], augmented['class_labels'])

        print(f"Augmented {img_file}")


if __name__ == "__main__":
    augment_directory(
        input_img_dir="PRIMARY Dataset/Images", 
        input_label_dir="PRIMARY Dataset/Labels",
        output_img_dir="Image_augmented/",
        output_label_dir="Label_augmented/",
        n_augments=1  
    )
