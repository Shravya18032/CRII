from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import os
import pandas as pd

# Load model
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Prompts
prompts = [
    "flooded region",
    "urban heat island",
    "dry vegetation",
    "dense urban area"
]

results = []

image_folder = "data/real_images"

for img_name in os.listdir(image_folder):
    img_path = os.path.join(image_folder, img_name)
    image = Image.open(img_path)

    inputs = processor(
        text=prompts,
        images=image,
        return_tensors="pt",
        padding=True
    )

    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1).detach().numpy()[0]

    results.append({
        "image": img_name,
        "flood_score": probs[0],
        "heat_score": probs[1],
        "vegetation_score": probs[2],
        "urban_score": probs[3]
    })

df = pd.DataFrame(results)
df.to_csv("data/clip_scores.csv", index=False)

print("CLIP scoring completed")