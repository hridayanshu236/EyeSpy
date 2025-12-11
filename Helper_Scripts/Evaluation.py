
import os
import cv2
import numpy as np
import albumentations as A
import torch
import torch.optim as optim
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_fscore_support
import sys
import torchvision.transforms.functional as TF
from models import (
    ObjectDetectionCNN,
    ObjectDetectionResNet,
    ObjectDetectionDenseNet121,
    ObjectDetectionMobileNetV2
)
RESIZE_SHAPE = (320, 320)
def collate_fn(batch):
    images, targets = zip(*batch)
    images = torch.stack(images)
    return images, list(targets)
class YOLODataset(Dataset):
    def __init__(self, images_dir, labels_dir, transform=None):
        self.images_dir = images_dir
        self.labels_dir = labels_dir
        self.transform = transform
        self.image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png'))]

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        # Load image
        img_filename = self.image_files[idx]
        img_path = os.path.join(self.images_dir, img_filename)
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        original_height, original_width, _ = image.shape

        # Load labels
        label_path = os.path.join(self.labels_dir, os.path.splitext(img_filename)[0] + ".txt")
        bboxes, class_labels = [], []

        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    class_id, x_c, y_c, w, h = map(float, line.strip().split())
                    x_min = max((x_c - w/2) * original_width, 0)
                    y_min = max((y_c - h/2) * original_height, 0)
                    x_max = min((x_c + w/2) * original_width, original_width - 1)
                    y_max = min((y_c + h/2) * original_height, original_height - 1)
                    # Filter invalid boxes
                    if x_max > x_min and y_max > y_min:
                        bboxes.append([x_min, y_min, x_max, y_max])
                        class_labels.append(int(class_id))

        # Apply transforms if available
        if self.transform and len(bboxes) > 0:
            try:
                transformed = self.transform(image=image, bboxes=bboxes, class_labels=class_labels)
                image = transformed['image']
                bboxes = transformed['bboxes']
                class_labels = transformed['class_labels']
            except ValueError as e:
                valid_bboxes, valid_labels = [], []
                for bbox, label in zip(bboxes, class_labels):
                    x_min, y_min, x_max, y_max = bbox
                    if x_max > x_min and y_max > y_min:
                        valid_bboxes.append(bbox)
                        valid_labels.append(label)
                if len(valid_bboxes) > 0:
                    try:
                        transformed = self.transform(image=image, bboxes=valid_bboxes, class_labels=valid_labels)
                        image = transformed['image']
                        bboxes = transformed['bboxes']
                        class_labels = transformed['class_labels']
                    except ValueError:

                        pass


        image = image / 255.0
        image = np.transpose(image, (2, 0, 1))  # HWC → CHW
        image = torch.tensor(image, dtype=torch.float32)


        current_height, current_width = image.shape[1], image.shape[2]
        image = TF.resize(image, RESIZE_SHAPE)
        new_height, new_width = RESIZE_SHAPE


        scale_x = new_width / current_width
        scale_y = new_height / current_height


        scaled_bboxes = []
        for bbox in bboxes:
            x_min, y_min, x_max, y_max = bbox
            scaled_x_min = x_min * scale_x
            scaled_y_min = y_min * scale_y
            scaled_x_max = x_max * scale_x
            scaled_y_max = y_max * scale_y

            # Clamp to image boundaries
            scaled_x_min = max(0, min(scaled_x_min, new_width - 1))
            scaled_y_min = max(0, min(scaled_y_min, new_height - 1))
            scaled_x_max = max(0, min(scaled_x_max, new_width - 1))
            scaled_y_max = max(0, min(scaled_y_max, new_height - 1))


            if scaled_x_max > scaled_x_min and scaled_y_max > scaled_y_min:
                scaled_bboxes.append([scaled_x_min, scaled_y_min, scaled_x_max, scaled_y_max])
            else:

                class_labels.pop(len(scaled_bboxes))


        targets = []
        for box, label in zip(scaled_bboxes, class_labels):
            targets.append([label] + list(box))
        targets = torch.tensor(targets, dtype=torch.float32) if targets else torch.zeros((0, 5), dtype=torch.float32)

        return image, targets
def draw_boxes(image, boxes, labels, color=(0, 255, 0), label_prefix=""):
    """Draw bounding boxes and labels on image"""
    image = image.copy()
    for box, label in zip(boxes, labels):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, f"{label_prefix}{label}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return image

def add_prediction_status(image, is_correct, position='top'):
    """Add prediction status text to image"""
    image = image.copy()
    status_text = "CORRECT PREDICTION" if is_correct else "INCORRECT PREDICTION"
    color = (0, 255, 0) if is_correct else (0, 0, 255)


    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    (text_width, text_height), baseline = cv2.getTextSize(status_text, font, font_scale, thickness)

    if position == 'top':
        x = (image.shape[1] - text_width) // 2
        y = text_height + 10
    else:
        x = (image.shape[1] - text_width) // 2
        y = image.shape[0] - 10


    cv2.rectangle(image, (x-5, y-text_height-5), (x+text_width+5, y+baseline+5), (255, 255, 255), -1)
    cv2.putText(image, status_text, (x, y), font, font_scale, color, thickness)

    return image

def evaluate_model_binary(model, test_loader, device, threshold=0.5, save_dir="pred_vs_true", max_images=100):
    os.makedirs(save_dir, exist_ok=True)
    model.eval()

    y_true =[]
    y_pred = []
    saved_count = 0

    print(f"Evaluating... (threshold={threshold})")

    with torch.no_grad():
        for batch_idx, (images, targets) in enumerate(test_loader):
            images = images.to(device)
            outputs = model(images)

            for i, (output, target) in enumerate(zip(outputs, targets)):

                if isinstance(target, torch.Tensor):
                    target = target.to(device)
                    true_class = 1 if (target.ndim == 2 and target.shape[0] > 0 and target[0, 0].item() > 0.5) else 0
                else:
                    continue


                pred_objectness = torch.sigmoid(output[0, 0]).item()
                pred_class = 1 if pred_objectness > threshold else 0

                y_true.append(true_class)
                y_pred.append(pred_class)


                if saved_count < max_images:
                    img_np = images[i].cpu().numpy().transpose(1, 2, 0) * 255
                    img_np = img_np.astype(np.uint8)
                    if img_np.shape[2] == 3:
                        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)


                    pred_boxes, pred_labels = [], []
                    for pred in output:
                        score = torch.sigmoid(pred[0]).item()
                        if score > threshold:
                            pred_boxes.append(pred[1:5].tolist())
                            pred_labels.append(f"P:{score:.2f}")


                    true_boxes, true_labels = [], []
                    if target.ndim == 2:
                        for t in target:
                            if len(t) >= 5:
                                _, x1, y1, x2, y2 = t.tolist()
                                true_boxes.append([x1, y1, x2, y2])
                                true_labels.append("GT")

                    pred_img = draw_boxes(img_np.copy(), pred_boxes, pred_labels, (0, 0, 255), "P:")
                    true_img = draw_boxes(img_np.copy(), true_boxes, true_labels, (0, 255, 0), "T:")

                    # Add comparison metadata
                    info_text = f"Pred: {pred_class} | True: {true_class} | Score: {pred_objectness:.2f}"
                    for img in [pred_img, true_img]:
                        cv2.putText(img, info_text, (10, img.shape[0] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

                    label_strip = np.zeros((30, img_np.shape[1], 3), dtype=np.uint8)
                    cv2.putText(label_strip, "GROUND TRUTH", (10, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    true_combined = np.vstack([label_strip, true_img])

                    label_strip_pred = label_strip.copy()
                    cv2.putText(label_strip_pred, "PREDICTION", (10, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    pred_combined = np.vstack([label_strip_pred, pred_img])

                    combined_img = np.concatenate([true_combined, pred_combined], axis=1)
                    cv2.imwrite(os.path.join(save_dir, f"CustomVGG_{saved_count:03d}.jpg"), combined_img)
                    saved_count += 1

            if (batch_idx + 1) % 5 == 0:
                acc = 100 * np.mean(np.array(y_true) == np.array(y_pred))
                print(f"Processed {batch_idx + 1} batches - Accuracy so far: {acc:.2f}%")


    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
    accuracy = 100 * np.mean(np.array(y_true) == np.array(y_pred))

    print("\n" + "="*60)
    print(f"Final Accuracy: {accuracy:.2f}%")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1:.2f}")
    print(f"Images saved to: {save_dir}")
    print("="*60)

    return {
        "accuracy": accuracy,
        "recall": recall,
        "f1_score": f1,
        "saved_images": saved_count
    }

def load_model(model_path, device):
    model = ObjectDetectionCNN().to(device)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    print(f"Model loaded from: {model_path}")
    print(f"Training was stopped at epoch: {checkpoint['epoch']}")
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

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    test_image_dir = "./test1/images"
test_label_dir = "./test1/labels"
test_transform = A.Compose([A.Resize(height=320, width=320, p=1.0)])
test_dataset = YOLODataset(
    images_dir=test_image_dir,
    labels_dir=test_label_dir,
    transform = test_transform
)

test_loader = DataLoader(
    test_dataset,
    batch_size=64,
    shuffle=True,
    collate_fn=collate_fn
)
model_path = "./Trained_Models/CustomVGG.pth" 
model = load_model(model_path,device)
save_path = "./CustomVGG_Predictions"
evaluate_model_binary(model,test_loader,device,0.4,save_path,20)
    