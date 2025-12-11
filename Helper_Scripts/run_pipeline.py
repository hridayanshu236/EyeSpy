import os
import cv2
from ultralytics import YOLO
from pathlib import Path

# Load the trained YOLOv8 model
model_path = "model/last.pt"
model = YOLO(model_path)

# Create output directories
os.makedirs("output/images", exist_ok=True)
os.makedirs("output/videos", exist_ok=True)

def process_image_folder(image_dir, output_dir):
    image_dir = Path(image_dir)
    for image_path in image_dir.glob("*.*"):
        if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
            continue
        results = model(image_path)
        for r in results:
            boxes = r.boxes
            top_indices = boxes.conf.argsort(descending=True)[:3] 
            boxes.data = boxes.data[top_indices]  

            annotated_img = r.plot()
            out_path = str(Path(output_dir) / image_path.name)
            cv2.imwrite(out_path, annotated_img)
            print(f"[IMAGE] Processed {image_path.name} with top 3 predictions")

def process_video_folder(video_dir, output_dir):
    video_dir = Path(video_dir)
    for video_path in video_dir.glob("*.*"):
        if video_path.suffix.lower() not in [".mp4", ".avi", ".mov", ".mkv"]:
            continue
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_path = str(Path(output_dir) / video_path.name)
        out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = model(frame)
            annotated_frame = results[0].plot()
            out.write(annotated_frame)

        cap.release()
        out.release()
        print(f"[VIDEO] Processed {video_path.name}")

if __name__ == "__main__":
    process_image_folder("input/images", "output/images")
    # process_video_folder("input/videos", "output/videos")
