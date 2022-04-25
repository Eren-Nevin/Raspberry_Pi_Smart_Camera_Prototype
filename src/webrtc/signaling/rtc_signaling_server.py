from pprint import pprint
import argparse
import asyncio
import ssl
import json
import logging
import uuid
import os
from typing import Dict, List

# from aiohttp import web
# ROOT = os.path.dirname(__file__)

from aiortc import RTCPeerConnection, RTCSessionDescription

from flask import Flask, request
from flask_socketio import SocketIO, emit, send, leave_room, join_room, \
    disconnect

# TODO: Write this either using websocket or a signaling system
# TODO: Add more error handling


logger = logging.getLogger("pc")


class Offer:
    def __init__(self, uid, d_uid, sdp, con_type, available):
        self.uid = uid
        self.d_uid = d_uid
        self.sdp = sdp
        self.con_type = con_type

    def __repr__(self):
        return f"{self.uid} to {self.d_uid}\n{self.sdp}\n*\n{self.con_type}"

offers: List[Offer] = []

def log_info(msg, *args):
    logger.info(pc_id + " " + msg, *args)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SOCKET_IO_SECRET_KEY'

socketio = SocketIO(app, logger=True,
                    # engineio_logger=True,
                    cors_allowed_origins="*",
                    )

try:

    @socketio.on('connect', namespace='/my_namespace')
    def on_connection():
        print("Connection Request")
        join_room('public')

    @socketio.on('disconnect', namespace='/my_namespace')
    def on_connection():
        print("Connection Disconnected")
        leave_room('public')

    @socketio.on('offer', namespace='/my_namespace')
    def handle_message(message):
        pprint(message)
        emit('new_offer', message, to='public')

    @socketio.on('answer', namespace='/my_namespace')
    def handle_message(message):
        pprint(message)
        emit('new_answer', message, to='public')

    @socketio.on('new_ice_candidate', namespace='/my_namespace')
    def handle_message(message):
        pprint(message)
        emit('new_ice_candidate', message, to='public', include_self=False)

except Exception:
    print("Exception")

if __name__ == "__main__":
    socketio.run(app, '0.0.0.0', 4311)
# async def index(request):
#     content = open(os.path.join(ROOT, "index.html"), "r").read()
#     return web.Response(content_type="text/html", text=content)


# async def javascript(request):
#     content = open(os.path.join(ROOT, "client.js"), "r").read()
#     return web.Response(content_type="application/javascript", text=content)

# async def im_available(request):
#     received_peer_dict = await request.json()
#     new_peer = Peer(received_peer_dict['uid'], received_peer_dict['sdp'],
#                     received_peer_dict['con_type'],
#                     received_peer_dict['available'])

#     peers[new_peer.uid] = new_peer
#     return web.Response(
#         content_type="application/json",
#         text=json.dumps(
#             {"status": 'OK',"Message": 'Added To Available Peers'}
#         ),
#     )

# async def im_unavailable(request):
#     peer_uid = (await request.json())['uid']
#     if peer_uid in peers:
#         removed_peer = peers.pop(peer_uid)
#         pprint(peers)
#         return web.Response(
#             content_type="application/json",
#             text=json.dumps(
#                 {"status": 'OK',"Message": 'Removed From Available Peers'}
#             ),
#         )
#     else:
#         return web.Response(
#             content_type="application/json",
#             text=json.dumps(
#                 {"status": 'OK',"Message": 'Peer Wasnt Registered'}
#             ),
#         )

# For now one device can only offer to connect to one other device not more

async def offer(request):
    m_received_offer = await request.json()
    if not m_received_offer:
        return "Error"

    received_offer = Offer(m_received_offer['uid'],
                           m_received_offer['destination_uid'],
                           m_received_offer['sdp'],
                           m_received_offer['con_type'])

    offers.append(received_offer)

async def answer(request):
    res = await request.json()
    if res == None:
        return "Error"

    answerer_uid = res['uid']

    print(f"{answerer_uid} is polling its callers")

    offer_to_answer = None

    for offer in offers:
        if offer.d_uid == answerer_uid:
            offer_to_answer = offer
            pprint(offer_to_answer)
            break

    if offer_to_answer:
    # Currently only offers are answered that the destination peer already
    # registered itself as available. In future you can be notified (e.g. using
    # websocket) whenever the destiantion device becomes available
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {
                    'status': 'OK',
                    'message': 'Caller Found',
                    'destination': {'uid': offer_to_answer.uid,
                                    "sdp": offer_to_answer.sdp,
                                    "type":offer_to_answer.con_type},
                }
            ),
        )
    else:
        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {'status': 'ERROR', 'message': 'No Caller Called'}
            ),
        )



    # Check for presence of keys

    # offer = RTCSessionDescription(sdp=received_offer_sdp,
    #                               type=received_offer_type)

    # pc = RTCPeerConnection()
    # pc_id = f"PeerConnection{uuid.uuid4()}"
    # pcs.add(pc)

    # log_info("Created for %s", request.host)
    # # PLAYER GOES HERE

    # @pc.on("datachannel")
    # def on_datachannel(channel):
    #     @channel.on("message")
    #     def on_message(message):
    #         if isinstance(message, str) and message.startswith("ping"):
    #             channel.send("pong" + message[4:])

    # @pc.on('connectionstatechange')
    # def on_connectionstatechange():
    #     print(f"Connection State Is {pc.connectionState}")

    # @pc.on("connectionstatechange")
    # async def on_connectionstatechange():
    #     log_info("Connection state is %s", pc.connectionState)
    #     if pc.connectionState == "failed":
    #         await pc.close()
    #         pcs.discard(pc)

    # # handle offer
    # await pc.setRemoteDescription(offer)

    # # send answer
    # answer = await pc.createAnswer()
    # await pc.setLocalDescription(answer)


# app.run('0.0.0.0', 4311)


    # app = web.Application()
    # app.router.add_get("/", index)
    # app.router.add_get("/client.js", javascript)
    # # app.router.add_post("/available", im_available)
    # # app.router.add_post("/unavailable", im_unavailable)
    # app.router.add_post("/offer", offer)
    # app.router.add_post("/answer", answer)
    # web.run_app(
    #     app, access_log=None, host='dinkedpawn.com', port=4322, ssl_context=None
    # )
