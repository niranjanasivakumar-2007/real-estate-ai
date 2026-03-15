from flask import Blueprint, request, session, jsonify
from config.db import properties_collection, images_collection
from bson import ObjectId

property_bp = Blueprint("property", __name__)


# --- GET ALL PROPERTIES (public, no login needed) ---
@property_bp.route("/properties", methods=["GET"])
def get_all_properties():
    try:
        from config.db import properties_collection as pc
        properties = list(pc.find())
        for p in properties:
            p["_id"] = str(p["_id"])
        return jsonify({"properties": properties, "count": len(properties)}), 200
    except Exception as e:
        return jsonify({"error": str(e), "properties": []}), 200


# --- GET SINGLE PROPERTY (public) ---
@property_bp.route("/properties/<property_id>", methods=["GET"])
def get_property(property_id):
    property_doc = properties_collection.find_one({"_id": ObjectId(property_id)})
    if not property_doc:
        return jsonify({"error": "Property not found"}), 404

    property_doc["_id"] = str(property_doc["_id"])

    # Get all images grouped by room
    images = list(images_collection.find({"property_id": property_id}))
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


# --- GET IMAGES BY ROOM TYPE (for buyer filtering) ---
@property_bp.route("/properties/<property_id>/rooms", methods=["GET"])
def get_rooms(property_id):
    room_type = request.args.get("room_type", "")

    query = {"property_id": property_id}
    if room_type:
        query["room_type"] = {"$regex": room_type, "$options": "i"}

    images = list(images_collection.find(query))
    grouped = {}
    for img in images:
        img["_id"] = str(img["_id"])
        room = img.get("room_type", "uncategorized")
        if room not in grouped:
            grouped[room] = []
        grouped[room].append(img)

    return jsonify({"rooms": grouped}), 200


# --- INCREMENT IMAGE VIEW ---
@property_bp.route("/properties/image/<image_id>/view", methods=["POST"])
def view_image(image_id):
    images_collection.update_one(
        {"_id": ObjectId(image_id)},
        {"$inc": {"views": 1}}
    )
    return jsonify({"message": "View recorded"}), 200


# --- LIKE AN IMAGE ---
@property_bp.route("/properties/image/<image_id>/like", methods=["POST"])
def like_image(image_id):
    images_collection.update_one(
        {"_id": ObjectId(image_id)},
        {"$inc": {"likes": 1}}
    )
    return jsonify({"message": "Image liked!"}), 200


# --- COMMENT ON IMAGE ---
@property_bp.route("/properties/image/<image_id>/comment", methods=["POST"])
def comment_image(image_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    comment = {
        "user": session.get("name", "Anonymous"),
        "text": data.get("text", "")
    }
    images_collection.update_one(
        {"_id": ObjectId(image_id)},
        {"$push": {"comments": comment}}
    )
    return jsonify({"message": "Comment added!"}), 200


# --- GET ALL STYLES (for filter dropdown) ---
@property_bp.route("/styles", methods=["GET"])
def get_styles():
    styles = images_collection.distinct("style")
    return jsonify({"styles": [s for s in styles if s]}), 200


# --- GET ALL ROOM TYPES (for filter dropdown) ---
@property_bp.route("/room-types", methods=["GET"])
def get_room_types():
    room_types = images_collection.distinct("room_type")
    return jsonify({"room_types": [r for r in room_types if r]}), 200
