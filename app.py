from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

users = {}  # Store user connections: {sid: nickname}
rooms = {}  # Store active chat rooms: {room_id: [user1, user2]}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def handle_connect():
    print(f"New connection: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    print(f"User disconnected: {request.sid}")
    # Remove user from room and users dict
    for room_id, participants in rooms.items():
        if request.sid in participants:
            participants.remove(request.sid)
            emit("system_message", "Your partner has disconnected.", to=room_id)
            if not participants:  # If room is empty, delete it
                del rooms[room_id]
            break
    users.pop(request.sid, None)

@socketio.on("set_nickname")
def set_nickname(nickname):
    users[request.sid] = nickname
    emit("system_message", f"Hello {nickname}! Waiting for a partner...", to=request.sid)
    assign_partner(request.sid)

def assign_partner(user_sid):
    print(f"Assigning partner for {user_sid}")
    for room_id, participants in rooms.items():
        print(f"Checking room {room_id}: {participants}")
        if len(participants) == 1:
            participants.append(user_sid)
            join_room(room_id)
            emit("system_message", "You are now connected to a partner!", to=room_id)
            print(f"Connected {user_sid} to room {room_id}")
            return
    room_id = f"room-{random.randint(1000, 9999)}"
    rooms[room_id] = [user_sid]
    join_room(room_id)
    print(f"Created new room {room_id} for {user_sid}")


@socketio.on("chat_message")
def handle_chat_message(data):
    room_id = None
    for rid, participants in rooms.items():
        if request.sid in participants:
            room_id = rid
            break
    if room_id:
        emit("chat_message", {"nickname": users[request.sid], "text": data}, to=room_id)


if __name__ == "__main__":
    socketio.run(app, debug=True)
