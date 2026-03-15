from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=7)
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

from routes.auth import auth_bp
from routes.seller import seller_bp
from routes.buyer import buyer_bp
from routes.property import property_bp

app.register_blueprint(auth_bp)
app.register_blueprint(seller_bp)
app.register_blueprint(buyer_bp)
app.register_blueprint(property_bp)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/buyer/dashboard")
def buyer_dashboard():
    return render_template("buyer_dashboard.html")

@app.route("/buyer/search")
def buyer_search_page():
    return render_template("search.html")

@app.route("/listing/<property_id>")
def listing_page(property_id):
    return render_template("listing.html")

@app.route("/seller/home")
def seller_dashboard_page():
    return render_template("seller_dashboard.html")

@app.route("/seller/home/upload")
def seller_upload_page():
    return render_template("upload.html")

@app.route("/seller-login")
def seller_login_page():
    return render_template("seller_login.html")

@app.route("/seller/dashboard/data", methods=["GET"])
def seller_dashboard_data():
    from routes.seller import seller_dashboard
    return seller_dashboard()

if __name__ == "__main__":
    app.run(debug=True)