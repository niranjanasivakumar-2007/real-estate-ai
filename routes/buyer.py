from flask import Blueprint, request, session, jsonify, send_file
from config.db import users_collection, properties_collection, images_collection
from bson import ObjectId


buyer_bp = Blueprint("buyer", __name__)

# --- HELPER: Check if buyer is logged in ---
def buyer_required():
    if "user_id" not in session or session.get("role") != "buyer":
        return False
    return True


# --- SEARCH PROPERTIES ---
@buyer_bp.route("/buyer/search", methods=["GET"])
def search_properties():
    if not buyer_required():
        return jsonify({"error": "Unauthorized"}), 401

    # Get search filters from query params
    location = request.args.get("location", "")
    budget_min = float(request.args.get("budget_min", 0))
    budget_max = float(request.args.get("budget_max", 99999999))
    room_type = request.args.get("room_type", "")
    style = request.args.get("style", "")

    # Build MongoDB query
    query = {}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if budget_min or budget_max:
        query["price"] = {"$gte": budget_min, "$lte": budget_max}

    properties = list(properties_collection.find(query))

    results = []
    for prop in properties:
        prop["_id"] = str(prop["_id"])
        property_id = prop["_id"]

        # Filter images by room_type and style if given
        image_query = {"property_id": property_id}
        if room_type:
            image_query["room_type"] = {"$regex": room_type, "$options": "i"}
        if style:
            image_query["style"] = {"$regex": style, "$options": "i"}

        images = list(images_collection.find(image_query))
        for img in images:
            img["_id"] = str(img["_id"])

        prop["images"] = images
        results.append(prop)

    return jsonify({"results": results}), 200


# --- VIEW PROPERTY DETAIL ---
@buyer_bp.route("/buyer/property/<property_id>", methods=["GET"])
def view_property(property_id):
    if not buyer_required():
        return jsonify({"error": "Unauthorized"}), 401

    # Increment view count
    properties_collection.update_one(
        {"_id": ObjectId(property_id)},
        {"$inc": {"views": 1}}
    )

    property_doc = properties_collection.find_one({"_id": ObjectId(property_id)})
    if not property_doc:
        return jsonify({"error": "Property not found"}), 404

    property_doc["_id"] = str(property_doc["_id"])

    # Get grouped images for this property
    images = list(images_collection.find({"property_id": property_id}))

    # Group images by room
    grouped = {}
    for img in images:
        img["_id"] = str(img["_id"])
        room = img.get("room_type", "uncategorized")
        if room not in grouped:
            grouped[room] = []
        grouped[room].append(img)

    return jsonify({
        "property": property_doc,
        "rooms": grouped
    }), 200


# --- LIKE A PROPERTY ---
@buyer_bp.route("/buyer/property/<property_id>/like", methods=["POST"])
def like_property(property_id):
    if not buyer_required():
        return jsonify({"error": "Unauthorized"}), 401

    properties_collection.update_one(
        {"_id": ObjectId(property_id)},
        {"$inc": {"likes": 1}}
    )
    return jsonify({"message": "Property liked!"}), 200


# --- COMMENT ON PROPERTY ---
@buyer_bp.route("/buyer/property/<property_id>/comment", methods=["POST"])
def comment_property(property_id):
    if not buyer_required():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    comment = {
        "user": session["name"],
        "text": data.get("text", "")
    }

    properties_collection.update_one(
        {"_id": ObjectId(property_id)},
        {"$push": {"comments": comment}}
    )
    return jsonify({"message": "Comment added!"}), 200


# --- UPDATE BUYER PREFERENCES ---
@buyer_bp.route("/buyer/preferences", methods=["PUT"])
def update_preferences():
    if not buyer_required():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    users_collection.update_one(
        {"firebase_uid": session["user_id"]},
        {"$set": {
            "preferences": {
                "location": data.get("location", ""),
                "budget_min": data.get("budget_min", 0),
                "budget_max": data.get("budget_max", 0),
                "land_size": data.get("land_size", ""),
                "design_idea_text": data.get("design_idea_text", "")
            }
        }}
    )
    return jsonify({"message": "Preferences updated!"}), 200


# --- VISUALIZE ROOM IMAGE ---
@buyer_bp.route("/buyer/visualize", methods=["GET"])
def visualize_image():
    image_url = request.args.get("image_url")
    color = request.args.get("color")
    lighting = request.args.get("lighting")
    style = request.args.get("style")

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    try:
        import requests as req
        from flask import send_file
        from ai.visualizer import visualize

        # Download image
        headers = {"User-Agent": "Mozilla/5.0"}
        img_response = req.get(image_url, headers=headers, timeout=10)
        if img_response.status_code != 200:
            return jsonify({"error": "Could not fetch image"}), 400

        image_bytes = img_response.content

        # Apply visualization
        result = visualize(image_bytes, color=color, lighting=lighting, style=style)

        if isinstance(result, bytes):
            from io import BytesIO
            result = BytesIO(result)
            result.seek(0)

        return send_file(result, mimetype="image/jpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # Download image from Cloudinary
    import requests as req
    from flask import send_file
    from ai.visualizer import visualize

    img_response = req.get(image_url)
    if img_response.status_code != 200:
        return jsonify({"error": "Could not fetch image"}), 400

    image_bytes = img_response.content

    # Apply visualization
    result = visualize(image_bytes, color=color, lighting=lighting, style=style)

    return send_file(result, mimetype="image/jpeg")