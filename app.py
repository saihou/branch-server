#!/usr/bin/env python

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import time
from datetime import datetime as dt
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import json
from pprint import pprint

DATA = None

with open('chat.json') as data_file:
    DATA = json.load(data_file)

pprint(DATA)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
room_name = 'main'

MESSAGES = {}
BRANCHES = []

@app.route('/')
def index():
    return render_template('index.html')

# As a user joins the room
@socketio.on('join', namespace='/branch')
def join(data):
    room = room_name
    username = data['username']
    join_room(room)
    print('joined room')

    # Initialize the record for this room if room is new
    global DATA
    # if room not in DATA.keys():
    #     print('hey')
    #     MESSAGES[room] = []
    #     BRANCHES.append(room)
    # # json = {}

    # for branch in BRANCHES:
    #     #print branch
    #     json[branch] = []

    #     messages_branch = []
    #     for message in MESSAGES[room]:
    #         if message['branch'] == branch:
    #             messages_branch.append(message)

    #     json[branch] = {'status': 'active',
    #                     'messages' : messages_branch}

    # print json # RETURN THIS

    # Emit every messages
    emit('joined room', {
        'username': username,
        'room': room,
        'chat': DATA
        },
        room=room)

    pprint(DATA)

# New message in a room
@socketio.on('room message', namespace='/branch')
def room_message(data):
    room = room_name
    username = data['username']
    message = data['message']
    if data['branch_name']:
        branch = data['branch_name']
    else:
        branch = room


    global DATA
    currTime = str(int(time.time()))

    # create new branch
    if branch not in DATA.keys():
        print 'Creating new branch'
        DATA[branch] = {
        'status': 'active',
        'openedTime': currTime,
        'date': currTime #FIXME date??
        }

        DATA[branch]['messages'] = []

    newMessage = {
            'username': username,
            'message': message
            }

    DATA[branch]['messages'].append(newMessage);

    # Emit every messages of this room
    emit('send room message', {
        'username': username,
        'message': message,
        'branch':branch
        },
        room=room)

    pprint(DATA)

# As a user leaves the room
@socketio.on('leave', namespace='/branch')
def leave(data):
    room = data['room']
    username = data['username']
    leave_room(room)
    emit('left room', {
        'username': username,
        'room': room
        },
        room=room)

# As a user disconnect
@socketio.on('disconnect request', namespace='branch')
def disconnect_request():
    emit('disconnected', {
        'message': 'Disconnected!'
        })
    disconnect()

@socketio.on('disconnect', namespace='/branch')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
