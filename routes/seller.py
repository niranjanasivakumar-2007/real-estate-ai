from flask import Blueprint, request, session, jsonify
from config.db import users_collection, properties_collection, images_collection
import cloudinary
import cloudinary.uploader
import os
from bson import ObjectId
import io
import urllib3
urllib3.disable_warnings()

seller_bp = Blueprint("seller", __name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def seller_required():
    if "user_id" not in session or session.get("role") != "seller":
        return False
    return True


# --- SELLER DASHBOARD ---
@seller_bp.route("/seller/dashboard", methods=["GET"])
def seller_dashboard():
    if not seller_required():
        return jsonify({"error": "Unauthorized"}), 401

    seller_id = session["user_id"]
    properties = list(properties_collection.find({"seller_id": seller_id}))
    for p in properties:
        p["_id"] = str(p["_id"])

    total_views = sum(p.get("views", 0) for p in properties)
    total_likes = sum(p.get("likes", 0) for p in properties)

    return jsonify({
        "name": session["name"],
        "total_properties": len(properties),
        "total_views": total_views,
        "total_likes": total_likes,
        "properties": properties
    }), 200


# --- UPLOAD PROPERTY ---
@seller_bp.route("/seller/upload", methods=["POST"])
def upload_property():
    if not seller_required():
        return jsonify({"error": "Unauthorized"}), 401

    seller_id = session["user_id"]

    title = request.form.get("title")
    location = request.form.get("location")
    price = request.form.get("price")
    land_size = request.form.get("land_size")
    description = request.form.get("description")

    if not title or not location or not price:
        return jsonify({"error": "Title, location and price are required"}), 400

    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "Please upload at least one image"}), 400

    # --- AI QUALITY CHECK EACH IMAGE FIRST ---
    from ai.quality_check import check_quality, quality_score

    passed_images = []
    rejected_images = []

    for file in files:
        filename = file.filename
        img_bytes = file.read()
        file.seek(0)

        result = check_quality(io.BytesIO(img_bytes))
        status = result["status"]

        if status == "rejected":
            rejected_images.append({
                "filename": filename,
                "reason": result["reason"]
            })

        elif status == "enhanced":
            # Use enhanced image bytes
            enhanced_io = result["enhanced_image"]
            enhanced_io.seek(0)
            enhanced_bytes = enhanced_io.read()
            passed_images.append({
                "filename": filename,
                "bytes": enhanced_bytes,
                "enhanced": True,
                "score": quality_score(
                    result["blur_score"],
                    result["brightness"]
                )
            })

        else:
            # Passed quality check
            passed_images.append({
                "filename": filename,
                "bytes": img_bytes,
                "enhanced": False,
                "score": quality_score(
                    result["blur_score"],
                    result["brightness"]
                )
            })

    # If ALL images rejected — stop and tell seller
    if not passed_images:
        return jsonify({
            "error": "all_rejected",
            "message": "All uploaded images failed quality check. Please upload clearer photos.",
            "rejected": rejected_images
        }), 400

    # Create property in MongoDB
    property_doc = {
        "seller_id": seller_id,
        "title": title,
        "location": location,
        "price": float(price),
        "land_size": land_size,
        "description": description,
        "views": 0,
        "likes": 0,
        "comments": [],
        "images": []
    }
    result = properties_collection.insert_one(property_doc)
    property_id = str(result.inserted_id)

    # Upload passed images to Cloudinary
    uploaded_images = []

    for img_data in passed_images:
        try:
            import base64
            img_base64 = base64.b64encode(img_data["bytes"]).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{img_base64}"
            upload_result = cloudinary.uploader.upload(
                   data_uri,
                   folder=f"real_estate/{property_id}",
                   resource_type="image",
                   timeout=60
            )
            image_url = upload_result["secure_url"]
            uploaded_images.append(image_url)

            image_doc = {
                "property_id": property_id,
                "seller_id": seller_id,
                "url": image_url,
                "cloudinary_id": upload_result["public_id"],
                "room_type": "room",
                "style": "modern",
                "group": "group_0",
                "quality_score": img_data["score"],
                "enhanced": img_data["enhanced"],
                "views": 0,
                "likes": 0,
                "comments": []
            }
            images_collection.insert_one(image_doc)

        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            return jsonify({"error": str(e)}), 500

    # Update property with image URLs
    properties_collection.update_one(
        {"_id": ObjectId(property_id)},
        {"$set": {"images": uploaded_images}}
    )

    # Build response — include info about rejected images if any
    response = {
        "message": "Property uploaded successfully!",
        "property_id": property_id,
        "images_uploaded": len(uploaded_images),
    }

    if rejected_images:
        response["warning"] = f"{len(rejected_images)} image(s) were rejected due to poor quality."
        response["rejected"] = rejected_images

    return jsonify(response), 201


# --- VIEW PROPERTY STATS ---
@seller_bp.route("/seller/property/<property_id>", methods=["GET"])
def property_stats(property_id):
    if not seller_required():
        return jsonify({"error": "Unauthorized"}), 401

    property_doc = properties_collection.find_one({"_id": ObjectId(property_id)})
    if not property_doc:
        return jsonify({"error": "Property not found"}), 404

    property_doc["_id"] = str(property_doc["_id"])
    images = list(images_collection.find({"property_id": property_id}))
    for img in images:
        img["_id"] = str(img["_id"])

    return jsonify({
        "property": property_doc,
        "images": images
    }), 200


# --- DELETE PROPERTY ---
@seller_bp.route("/seller/property/<property_id>", methods=["DELETE"])
def delete_property(property_id):
    if not seller_required():
        return jsonify({"error": "Unauthorized"}), 401

    images = list(images_collection.find({"property_id": property_id}))
    for img in images:
        try:
            cloudinary.uploader.destroy(img["cloudinary_id"])
        except:
            pass

    images_collection.delete_many({"property_id": property_id})
    properties_collection.delete_one({"_id": ObjectId(property_id)})

    return jsonify({"message": "Property deleted successfully!"}), 200