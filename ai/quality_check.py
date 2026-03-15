import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io

# --- CHECK IMAGE QUALITY ---
def check_quality(image_file):
    # Read image
    img_bytes = image_file.read()
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"status": "rejected", "reason": "Cannot read image"}

    # Check 1 — Blur detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Check 2 — Brightness
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    brightness = hsv[:, :, 2].mean()

    # Check 3 — Resolution
    height, width = img.shape[:2]
    resolution_ok = width >= 100 and height >= 100

    # Scoring
    issues = []
    if blur_score < 20:
        issues.append("too_blurry")
    if brightness < 20:
        issues.append("too_dark")
    if brightness > 240:
        issues.append("too_bright")
    if not resolution_ok:
        issues.append("low_resolution")

    # Decide outcome
    if "low_resolution" in issues or len(issues) >= 2:
        return {
            "status": "rejected",
            "reason": ", ".join(issues),
            "blur_score": blur_score,
            "brightness": brightness
        }

    if issues:
        # Try to auto enhance
        enhanced = auto_enhance(img_bytes, issues)
        return {
            "status": "enhanced",
            "issues_fixed": issues,
            "enhanced_image": enhanced,
            "blur_score": blur_score,
            "brightness": brightness
        }

    return {
        "status": "passed",
        "blur_score": blur_score,
        "brightness": brightness
    }


# --- AUTO ENHANCE IMAGE ---
def auto_enhance(img_bytes, issues):
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    if "too_dark" in issues:
        enhancer = ImageEnhance.Brightness(pil_img)
        pil_img = enhancer.enhance(1.6)

    if "too_bright" in issues:
        enhancer = ImageEnhance.Brightness(pil_img)
        pil_img = enhancer.enhance(0.7)

    if "too_blurry" in issues:
        enhancer = ImageEnhance.Sharpness(pil_img)
        pil_img = enhancer.enhance(2.0)

    # Convert back to bytes
    output = io.BytesIO()
    pil_img.save(output, format="JPEG", quality=90)
    output.seek(0)
    return output


# --- QUALITY SCORE (0-100) ---
def quality_score(blur_score, brightness):
    blur_norm = min(blur_score / 500 * 50, 50)
    bright_norm = max(0, 50 - abs(brightness - 130) / 130 * 50)
    return round(blur_norm + bright_norm, 2)
