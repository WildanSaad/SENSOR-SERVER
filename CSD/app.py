from flask import Flask, request, jsonify, send_from_directory
from models import db, User, SensorData, UserLocation
from datetime import datetime
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
import math

# إنشاء التطبيق
app = Flask(__name__, static_folder="", static_url_path="")
CORS(app)

# إعداد قاعدة البيانات (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# إنشاء الجداول إذا ما موجودة
with app.app_context():
    db.create_all()

# ------------------ Serve HTML ------------------
@app.route('/')
def root():
    return send_from_directory(os.getcwd(), 'welcome.html')

@app.route('/<path:filename>')
def serve_html(filename):
    return send_from_directory(os.getcwd(), filename)

# ------------------ Admin Register ------------------
@app.route('/admin-register', methods=['POST'])
def admin_register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    if User.query.filter_by(username=username, role="admin").first():
        return jsonify({"message": "Username already exists", "error": "username"}), 409

    admins = User.query.filter_by(role="admin").all()
    for adm in admins:
        if check_password_hash(adm.password, password):
            return jsonify({"message": "Password already used", "error": "password"}), 409

    hashed_pw = generate_password_hash(password)
    new_admin = User(
        name=username,
        username=username,
        password=hashed_pw,
        role="admin",
        user_type="admin",
        location=""
    )
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({"message": "Admin account created successfully"}), 201

# ------------------ Admin Login ------------------
@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, role="admin").first()
    if not user:
        return jsonify({"message": "Incorrect username", "error": "username"}), 401

    if not password or not check_password_hash(user.password, password):
        return jsonify({"message": "Incorrect password", "error": "password"}), 401

    return jsonify({"message": "Login successful", "role": "admin"}), 200

# ------------------ Sensor data (create) ------------------
@app.route('/sensor', methods=['POST'])
def receive_sensor():
    data = request.json or {}
    required = ['sensor_id', 'sensor_type', 'location', 'value']
    if any(k not in data or data[k] is None or str(data[k]).strip() == "" for k in required):
        return jsonify({"message": "All fields are required"}), 400

    existing = SensorData.query.filter_by(sensor_id=data['sensor_id']).first()
    if existing:
        return jsonify({"message": "Sensor ID already exists, must be unique"}), 400

    new_data = SensorData(
        sensor_id=data['sensor_id'],
        sensor_type=data['sensor_type'],
        location=data['location'],
        value=str(data['value']),
        timestamp=datetime.now()
    )
    db.session.add(new_data)
    db.session.commit()
    return jsonify({"message": "Data stored successfully"}), 201

# ------------------ Add user location ------------------
@app.route('/add-location', methods=['POST'])
def add_location():
    data = request.json or {}
    required = ['latitude', 'longitude']
    if any(k not in data or str(data[k]).strip() == "" for k in required):
        return jsonify({"message": "Missing fields"}), 400

    # إنشاء مستخدم عادي تلقائيًا لكل إرسال
    generated_username = f"user_{secrets.token_hex(8)}"
    generated_password_hash = generate_password_hash(secrets.token_urlsafe(16))

    new_user = User(
        name=generated_username,
        username=generated_username,
        password=generated_password_hash,
        role="user",
        user_type="user",
        location=""
    )
    db.session.add(new_user)
    db.session.flush()

    lat = float(data['latitude'])
    lng = float(data['longitude'])

    new_loc = UserLocation(
        user_id=new_user.id,
        latitude=lat,
        longitude=lng,
        timestamp=datetime.now()
    )
    db.session.add(new_loc)

    # مقارنة مع الحساسات
    alerts = []
    sensors = SensorData.query.all()
    for s in sensors:
        try:
            s_lat, s_lng = map(float, s.location.split(","))
            distance = math.sqrt((lat - s_lat)**2 + (lng - s_lng)**2)
            if distance < 0.001:  # تقريباً ~100 متر
                alerts.append(f"Near sensor {s.sensor_id}")
        except:
            continue

    db.session.commit()

    return jsonify({
        "message": "Location added",
        "user_id": new_user.id,
        "username": new_user.username,
        "alerts": alerts
    }), 201

# ------------------ Get users ------------------
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "username": u.username,
            "role": u.role,
            "user_type": u.user_type,
            "location": u.location
        }
        for u in users
    ])

# ------------------ Delete user (any role) ------------------
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} deleted successfully"}), 200

# ------------------ Get user locations ------------------
@app.route('/user-locations', methods=['GET'])
def get_user_locations():
    locs = UserLocation.query.all()
    return jsonify([
        {
            "id": l.id,
            "user_id": l.user_id,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in locs
    ])

# ------------------ Get sensor data ------------------
@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    data = SensorData.query.all()
    return jsonify([
        {
            "id": d.id,
            "sensor_id": d.sensor_id,
            "sensor_type": d.sensor_type,
            "location": d.location,
            "value": d.value,
            "timestamp": d.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for d in data
    ])

# ------------------ Delete sensor ------------------
@app.route('/sensor/<sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    sensor = SensorData.query.filter_by(sensor_id=sensor_id).first()
    if not sensor:
        return jsonify({"message": "Sensor not found"}), 404

    db.session.delete(sensor)
    db.session.commit()
    return jsonify({"message": f"Sensor {sensor_id} deleted successfully"}), 200

# ------------------ Run server ------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)