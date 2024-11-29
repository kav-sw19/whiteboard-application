from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO, emit
from datetime import datetime
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'passwordpleasedontsteal!'
socketio = SocketIO(app)

# Single default room
DEFAULT_ROOM = "MAIN"

USER_COLORS = {
    0: "#000000",    # Black
    1: "#4B6F44",    # Kashmir green
    2: "#191970",    # Midnight blue
    3: "#8A3324",    # Burnt umber
    4: "#228B22",    # Forest green
    5: "#000080",    # Navy blue
    6: "#8B4513",    # Deep burnt sienna
    7: "#4B0082",    # Indigo blue
    8: "#40826D",    # Viridian green
    9: "#003153",    # Prussian blue
    10: "#800020",   # Deep burgundy
}

rooms = {
    DEFAULT_ROOM: {
        "members": [], 
        "messages": [], 
        "member_colors": {},  # Will store name: color mappings
        "color_index": 0,     # Keeps track of next color to assign
        "drawings": []  # Store drawing data
    }
}

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')

        if not name:
            return render_template('home.html', error="Please enter a name.", name=name)
        
        session['room'] = DEFAULT_ROOM
        session['name'] = name
 
        return redirect(url_for('room'))
    
    return render_template('home.html')

@app.route('/room')
def room():
    if session.get('name') is None:
        return redirect(url_for('home'))

    members = [session.get('name')]
    for member in rooms[DEFAULT_ROOM]['members']:
        if member != session.get('name'):
            members.append(member)

    return render_template('room.html', 
        messages=rooms[DEFAULT_ROOM]['messages'], 
        members=members,
        rooms=rooms,
        DEFAULT_ROOM=DEFAULT_ROOM
    )

@socketio.on('connect')
def connect(auth):
    name = session.get('name')
    if not name:
        return

    join_room(DEFAULT_ROOM)
    
    color_idx = rooms[DEFAULT_ROOM]['color_index'] % len(USER_COLORS)
    rooms[DEFAULT_ROOM]['member_colors'][name] = USER_COLORS[color_idx]
    rooms[DEFAULT_ROOM]['color_index'] += 1
    
    send({
        "name": name, 
        "message": "has entered the room",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "color": "#808080",
        "type": "system"
    }, to=DEFAULT_ROOM)
    
    rooms[DEFAULT_ROOM]['members'].append(name)
    
    emit('update_members', {
        'members': rooms[DEFAULT_ROOM]['members'],
        'colors': rooms[DEFAULT_ROOM]['member_colors']
    }, to=DEFAULT_ROOM)
    
    # Send existing drawings to new user
    emit('load_drawings', rooms[DEFAULT_ROOM]['drawings'], to=request.sid)
    
    print(f"{name} joined the room")

@socketio.on('disconnect')
def disconnect():
    name = session.get('name')
    leave_room(DEFAULT_ROOM)

    if name in rooms[DEFAULT_ROOM]['members']:
        rooms[DEFAULT_ROOM]['members'].remove(name)
        
        # Clear messages if this was the last person
        if not rooms[DEFAULT_ROOM]['members']:
            rooms[DEFAULT_ROOM]['messages'] = []
            rooms[DEFAULT_ROOM]['member_colors'] = {}
            rooms[DEFAULT_ROOM]['color_index'] = 0
        
        emit('update_members', {
            'members': rooms[DEFAULT_ROOM]['members'],
            'colors': rooms[DEFAULT_ROOM]['member_colors']
        }, to=DEFAULT_ROOM)

    send({
        "name": name, 
        "message": "has left the room",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "color": "#808080",
        "type": "system"
    }, to=DEFAULT_ROOM)
    print(f"{name} has left the room")

@socketio.on('message')
def message(data):
    name = session.get('name')
    content = {
        "name": name,
        "message": data.get('data'),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "color": rooms[DEFAULT_ROOM]['member_colors'].get(name, "#000000")
    }
    send(content, to=DEFAULT_ROOM)
    rooms[DEFAULT_ROOM]['messages'].append(content)
    print(f"{session.get('name')} said: {data.get('data')} at {content['timestamp']}")

@socketio.on('draw')
def handle_draw(data):
    # Broadcast the drawing data to all users in the room
    emit('draw', data, room=DEFAULT_ROOM)
    rooms[DEFAULT_ROOM]['drawings'].append(data)

@socketio.on('clear_canvas')
def handle_clear():
    # Clear the canvas for all users
    rooms[DEFAULT_ROOM]['drawings'] = []
    emit('clear_canvas', room=DEFAULT_ROOM)

if __name__ == '__main__':
    socketio.run(app, debug=True)