import argparse
import asyncio
import ssl
import json
import logging
import uuid
import os
# from flask import Flask, request

from aiohttp import web


from aiortc import RTCPeerConnection, RTCSessionDescription

# app = Flask(__name__, static_folder='./org', static_url_path='/')

logger = logging.getLogger("pc")
pcs = set()

ROOT = os.path.dirname(__file__)

async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

# @app.route('/offer', methods=['POST'])

async def offer(request):
    params = await request.json()
    if params == None:
        return "Error"

    # Check for presence of keys

    received_offer_sdp = params['sdp']
    # print(received_offer_sdp)

    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

    pc = RTCPeerConnection()
    pc_id = f"PeerConnection{uuid.uuid4()}"
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.host)

    # PLAYER GOES HERE

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on('connectionstatechange')
    def on_connectionstatechange():
        print(f"Connection State Is {pc.connectionState}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # handle offer
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

# app.run('0.0.0.0', 4311)

if __name__ == "__main__":

    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(
        app, access_log=None, host='0.0.0.0', port=4322, ssl_context=None
    )
