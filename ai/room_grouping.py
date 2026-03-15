# Lazy imports — only load when actually used
def get_embedding(image_bytes):
    import torch
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel
    import io
    import numpy as np

    global clip_model, clip_processor
    try:
        clip_model
    except NameError:
        clip_model = None
        clip_processor = None

    if clip_model is None:
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = clip_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        embedding = clip_model.get_image_features(**inputs)
    embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding.squeeze().numpy()


def cosine_similarity(vec1, vec2):
    import numpy as np
    return float(np.dot(vec1, vec2))


def group_images(image_files):
    embeddings = []
    for f in image_files:
        img_bytes = f.read()
        emb = get_embedding(img_bytes)
        embeddings.append(emb)
        f.seek(0)

    n = len(embeddings)
    visited = [False] * n
    groups = {}
    group_id = 0
    threshold = 0.85

    for i in range(n):
        if visited[i]:
            continue
        group = [i]
        visited[i] = True
        for j in range(i + 1, n):
            if not visited[j]:
                sim = cosine_similarity(embeddings[i], embeddings[j])
                if sim > threshold:
                    group.append(j)
                    visited[j] = True
        groups[f"group_{group_id}"] = group
        group_id += 1

    return groups


def assign_groups(image_files):
    groups = group_images(image_files)
    labels = [""] * len(image_files)
    for group_name, indices in groups.items():
        for idx in indices:
            labels[idx] = group_name
    return labels