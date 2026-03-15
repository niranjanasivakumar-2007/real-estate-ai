from flask import Blueprint, request, session, jsonify
from config.db import users_collection, partnership_codes_collection
import requests
import os

auth_bp = Blueprint("auth", __name__)

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

# --- BUYER SIGNUP ---
@auth_bp.route("/buyer/signup", methods=["POST"])
def buyer_signup():
    data = request.json

    # Step 1 — Create user in Firebase
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    firebase_res = requests.post(firebase_url, json={
        "email": data["email"],
        "password": data["password"],
        "returnSecureToken": True
    })
    firebase_data = firebase_res.json()

    if "error" in firebase_data:
        return jsonify({"error": firebase_data["error"]["message"]}), 400

    # Step 2 — Save extra details in MongoDB
    user = {
        "firebase_uid": firebase_data["localId"],
        "name": data["name"],
        "email": data["email"],
        "phone": data["phone"],
        "role": "buyer",
        "preferences": {
            "location": data.get("location", ""),
            "budget_min": data.get("budget_min", 0),
            "budget_max": data.get("budget_max", 0),
            "land_size": data.get("land_size", ""),
            "design_idea_text": data.get("design_idea_text", "")
        }
    }
    users_collection.insert_one(user)
    return jsonify({"message": "Buyer registered successfully!"}), 201


# --- BUYER LOGIN ---
@auth_bp.route("/buyer/login", methods=["POST"])
def buyer_login():
    data = request.json

    # Firebase login
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    firebase_res = requests.post(firebase_url, json={
        "email": data["email"],
        "password": data["password"],
        "returnSecureToken": True
    })
    firebase_data = firebase_res.json()

    if "error" in firebase_data:
        return jsonify({"error": firebase_data["error"]["message"]}), 401

    # Get extra details from MongoDB
    user = users_collection.find_one({"firebase_uid": firebase_data["localId"]})
    if not user or user["role"] != "buyer":
        return jsonify({"error": "Not registered as a buyer"}), 403

    session["user_id"] = firebase_data["localId"]
    session["role"] = "buyer"
    session["name"] = user["name"]
    return jsonify({"message": "Login successful!", "name": user["name"]}), 200


# --- SELLER LOGIN (partnership code required) ---
@auth_bp.route("/seller/login", methods=["POST"])
def seller_login():
    data = request.json

    # Check partnership code first
    code_entry = partnership_codes_collection.find_one({"code": data["partnership_code"]})
    if not code_entry:
        return jsonify({"error": "Invalid partnership code"}), 403

    # Firebase login
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    firebase_res = requests.post(firebase_url, json={
        "email": data["email"],
        "password": data["password"],
        "returnSecureToken": True
    })
    firebase_data = firebase_res.json()

    if "error" in firebase_data:
        return jsonify({"error": firebase_data["error"]["message"]}), 401

    # Get seller details from MongoDB
    user = users_collection.find_one({"firebase_uid": firebase_data["localId"]})
    if not user or user["role"] != "seller":
        return jsonify({"error": "Not registered as a seller"}), 403

    session["user_id"] = firebase_data["localId"]
    session["role"] = "seller"
    session["name"] = user["name"]
    return jsonify({"message": "Seller login successful!", "name": user["name"]}), 200


# --- LOGOUT ---
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# --- CHECK SESSION ---
@auth_bp.route("/session", methods=["GET"])
def check_session():
    if "user_id" in session:
        return jsonify({
            "logged_in": True,
            "role": session["role"],
            "name": session["name"]
        }), 200
    return jsonify({"logged_in": False}), 200
