from PIL import Image, ImageFilter, ImageEnhance
import io
import numpy as np
import cv2

# --- CHANGE ROOM COLOR ---
def change_room_color(image_bytes, target_color):
    color_map = {
        "pink":   (255, 182, 193),
        "blue":   (135, 206, 235),
        "white":  (255, 255, 255),
        "green":  (144, 238, 144),
        "yellow": (255, 255, 153),
        "gray":   (200, 200, 200),
        "beige":  (245, 245, 220),
        "brown":  (181, 101, 29),
        "red":    (255, 99, 71),
        "purple": (216, 191, 216),
        "orange": (255, 200, 124),
        "black":  (40, 40, 40)
    }

    target_rgb = color_map.get(target_color.lower(), (255, 255, 255))

    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(pil_img, dtype=np.float32)

    img_cv = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_RGB2HSV)
    saturation = img_cv[:, :, 1]
    brightness = img_cv[:, :, 2]
    wall_mask = (saturation < 60) & (brightness > 100)

    target_r, target_g, target_b = target_rgb
    img_array[wall_mask, 0] = target_r * 0.6 + img_array[wall_mask, 0] * 0.4
    img_array[wall_mask, 1] = target_g * 0.6 + img_array[wall_mask, 1] * 0.4
    img_array[wall_mask, 2] = target_b * 0.6 + img_array[wall_mask, 2] * 0.4

    result_img = Image.fromarray(img_array.astype(np.uint8))
    result_img = result_img.filter(ImageFilter.SMOOTH)

    output = io.BytesIO()
    result_img.save(output, format="JPEG", quality=90)
    output.seek(0)
    return output.read()


# --- CHANGE LIGHTING ---
def change_lighting(image_bytes, mood):
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(pil_img, dtype=np.float32)

    if mood == "warm":
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.2, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.8, 0, 255)
    elif mood == "cool":
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.2, 0, 255)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.8, 0, 255)
    elif mood == "bright":
        img_array = np.clip(img_array * 1.3, 0, 255)
    elif mood == "dim":
        img_array = np.clip(img_array * 0.7, 0, 255)

    result_img = Image.fromarray(img_array.astype(np.uint8))
    output = io.BytesIO()
    result_img.save(output, format="JPEG", quality=90)
    output.seek(0)
    return output.read()


# --- APPLY STYLE FILTER ---
def apply_style_filter(image_bytes, style):
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(pil_img, dtype=np.float32)

    if style == "minimalist":
        gray = np.mean(img_array, axis=2, keepdims=True)
        img_array = img_array * 0.4 + gray * 0.6
        img_array = np.clip(img_array * 1.1, 0, 255)
    elif style == "warm":
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.15, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.05, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.85, 0, 255)
    elif style == "vintage":
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.1, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.95, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.75, 0, 255)
        img_array = np.clip(img_array * 0.9 + 20, 0, 255)
    elif style == "bright":
        img_array = np.clip(img_array * 1.25, 0, 255)

    result_img = Image.fromarray(img_array.astype(np.uint8))
    output = io.BytesIO()
    result_img.save(output, format="JPEG", quality=90)
    output.seek(0)
    return output.read()


# --- MASTER VISUALIZE FUNCTION ---
def visualize(image_bytes, color=None, lighting=None, style=None):
    result = image_bytes

    if color:
        result = change_room_color(result, color)
    if lighting:
        result = change_lighting(result, lighting)
    if style:
        result = apply_style_filter(result, style)

    from io import BytesIO
    final = BytesIO(result)
    final.seek(0)
    return final