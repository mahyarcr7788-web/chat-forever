from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}  # username: password_hash
private_rooms = {}  # room_name: {"password": password, "users": set(), "messages": []}
global_room = "global"

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("chat"))
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"].strip()
    password = request.form["password"]
    if not username or not password:
        return "Please provide username and password.", 400
    if username in users:
        return "Username already exists.", 400
    users[username] = generate_password_hash(password)
    session["username"] = username
    return redirect(url_for("chat"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"].strip()
    password = request.form["password"]
    if username not in users or not check_password_hash(users[username], password):
        return "Invalid username or password.", 400
    session["username"] = username
    return redirect(url_for("chat"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("index"))
    return render_template("chat.html", username=session["username"])

@app.route("/create_room", methods=["POST"])
def create_room():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    room_name = data.get("room_name", "").strip()
    password = data.get("password", "").strip()
    if not room_name or not password:
        return jsonify({"error": "Room name and password required"}), 400
    if room_name == global_room:
        return jsonify({"error": "Room name reserved"}), 400
    if room_name in private_rooms:
        return jsonify({"error": "Room already exists"}), 400
    private_rooms[room_name] = {"password": password, "users": set(), "messages": []}
    return jsonify({"success": True})

@app.route("/join_room", methods=["POST"])
def join_room_api():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    room_name = data.get("room_name", "").strip()
    password = data.get("password", "").strip()
    if not room_name or not password:
        return jsonify({"error": "Room name and password required"}), 400
    if room_name == global_room:
        return jsonify({"error": "Use the global chat directly"}), 400
    if room_name not in private_rooms:
        return jsonify({"error": "Room does not exist"}), 404
    if private_rooms[room_name]["password"] != password:
        return jsonify({"error": "Incorrect password"}), 403
    return jsonify({"success": True})

@socketio.on("join")
def on_join(data):
    username = session.get("username")
    room = data.get("room")
    if not username or not room:
        return
    if room == global_room:
        join_room(global_room)
        emit("status", f"{username} has joined the Global chat.", room=global_room)
        private_rooms.setdefault(global_room, {"password": None, "users": set(), "messages": []})
        private_rooms[global_room]["users"].add(username)
        join_room(room)
        emit("chat_history", private_rooms[global_room]["messages"], room=request.sid)
    else:
        # Private room join
        if room not in private_rooms:
            return
        join_room(room)
        private_rooms[room]["users"].add(username)
        emit("status", f"{username} has joined the room {room}.", room=room)
        emit("chat_history", private_rooms[room]["messages"], room=request.sid)

@socketio.on("leave")
def on_leave(data):
    username = session.get("username")
    room = data.get("room")
    if not username or not room:
        return
    leave_room(room)
    if room in private_rooms and username in private_rooms[room]["users"]:
        private_rooms[room]["users"].remove(username)
        emit("status", f"{username} has left the room.", room=room)
        if room != global_room and len(private_rooms[room]["users"]) == 0:
            del private_rooms[room]

@socketio.on("message")
def on_message(data):
    username = session.get("username")
    room = data.get("room")
    text = data.get("message")
    if not username or not room or not text:
        return
    msg_obj = {"user": username, "text": text}
    if room not in private_rooms:
        return
    private_rooms[room]["messages"].append(msg_obj)
    emit("message", msg_obj, room=room)

if __name__ == "__main__":
    private_rooms[global_room] = {"password": None, "users": set(), "messages": []}
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)

