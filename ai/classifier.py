ROOM_TYPES = [
    "bedroom", "kitchen", "living room", "bathroom",
    "dining room", "balcony", "garden", "garage",
    "home office", "hallway"
]

STYLES = [
    "modern", "minimalist", "farmhouse", "traditional",
    "industrial", "bohemian", "scandinavian", "luxury",
    "rustic", "contemporary"
]

clip_model = None
clip_processor = None

def load_clip():
    global clip_model, clip_processor
    if clip_model is None:
        import torch
        from transformers import CLIPProcessor, CLIPModel
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def classify_room(image_bytes):
    import torch
    from PIL import Image
    import io
    load_clip()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    prompts = [f"a photo of a {room}" for room in ROOM_TYPES]
    inputs = clip_processor(
        text=prompts, images=image,
        return_tensors="pt", padding=True
    )
    with torch.no_grad():
        outputs = clip_model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
    best_idx = probs.argmax().item()
    return {
        "room_type": ROOM_TYPES[best_idx],
        "confidence": round(probs[0][best_idx].item() * 100, 2)
    }


def classify_style(image_bytes):
    import torch
    from PIL import Image
    import io
    load_clip()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    prompts = [f"a {style} style interior design" for style in STYLES]
    inputs = clip_processor(
        text=prompts, images=image,
        return_tensors="pt", padding=True
    )
    with torch.no_grad():
        outputs = clip_model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
    best_idx = probs.argmax().item()
    return {
        "style": STYLES[best_idx],
        "confidence": round(probs[0][best_idx].item() * 100, 2)
    }


def classify_image(image_bytes):
    room_result = classify_room(image_bytes)
    style_result = classify_style(image_bytes)
    return {
        "room_type": room_result["room_type"],
        "room_confidence": room_result["confidence"],
        "style": style_result["style"],
        "style_confidence": style_result["confidence"]
    }