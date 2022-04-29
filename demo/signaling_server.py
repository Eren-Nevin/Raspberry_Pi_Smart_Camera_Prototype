from pprint import pprint
import asyncio
import ssl
import json
import logging
import sys

# from aiohttp import web

from flask import Flask, request, render_template, send_file
from flask_socketio import SocketIO, emit, send, leave_room, join_room

# TODO: Write this either using websocket or a signaling system
# TODO: Add more error handling


class Offer:
    def __init__(self, uid, d_uid, sdp, con_type):
        self.uid = uid
        self.d_uid = d_uid
        self.sdp = sdp
        self.con_type = con_type

    def __repr__(self):
        return f"{self.uid} to {self.d_uid}\n{self.sdp}\n*\n{self.con_type}"

# app = Flask(__name__, static_folder='.', static_url_path='/')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SOCKET_IO_SECRET_KEY'

socket_io_namespace = sys.argv[1]

socketio = SocketIO(app, logger=True,
                    # engineio_logger=True,
                    cors_allowed_origins="*",
                    )
@app.route('/')
def index():
    m_response = send_file('./live_cam.html', etag=False)
    m_response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    m_response.headers["Expires"] = '0'
    m_response.headers["Pragma"] = "no-cache"
    return m_response
    # return render_template('live_cam.html')
    # return "Hello World"

@app.route('/live_cam.js')
def serve_js():
    m_response = send_file('./live_cam.js', etag=False)
    m_response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    m_response.headers["Expires"] = '0'
    m_response.headers["Pragma"] = "no-cache"
    return m_response

print("Started Websocket")
try:

    @socketio.on('connect', namespace=f"/{socket_io_namespace}")
    def on_connect():
        print("Connection Request")
        join_room('public')

    @socketio.on('disconnect', namespace=f"/{socket_io_namespace}")
    def on_disonnect():
        print("Connection Disconnected")
        leave_room('public')

    @socketio.on('offer', namespace=f"/{socket_io_namespace}")
    def handle_offer(message):
        pprint(message)
        emit('new_offer', message, to='public')

    @socketio.on('answer', namespace=f"/{socket_io_namespace}")
    def handle_answer(message):
        pprint(message)
        emit('new_answer', message, to='public')

    @socketio.on('new_ice_candidate', namespace=f"/{socket_io_namespace}")
    def handle_ice_candidate(message):
        pprint(message)
        emit('new_ice_candidate', message, to='public', include_self=False)

except Exception:
    print("Exception")

if __name__ == "__main__":
    socketio.run(app, '0.0.0.0', 4311)
    # app.run('0.0.0.0', 4311)
