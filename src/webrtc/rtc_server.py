import asyncio
import json
from logging import INFO, log
import uuid
from flask import Flask, request


from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRecorder, MediaRelay

relay = MediaRelay()

app = Flask(__name__, static_folder='./client', static_url_path='/')

# player = MediaPlayer('/dev/video0', format='v4l2', options={'video_size':
#                                                            '640x480'})

# We're actually answering an offer from browser


@app.route('/offer', methods=['POST'])
async def offer():
    params = request.json
    if params == None:
        return "Error"

    # Check for presence of keys

    received_offer_sdp = params['sdp']
    print(received_offer_sdp)

    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

    pc = RTCPeerConnection()
    pc_id = f"PeerConnection{uuid.uuid4()}"

    print(f"Created for {request.host}")
    # PLAYER GOES HERE

    @pc.on('datachannel')
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print(f"Got {message}")
            if isinstance(message, str):
                channel.send(f"Got {message}")


    @pc.on('connectionstatechange')
    def on_connectionstatechange():
        print(f"Connection State Is {pc.connectionState}")

    # pc.setRemoteDescription()
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    if answer == None:
        return "Error"

    await pc.setLocalDescription(answer)

    # print(pc.localDescription.sdp)

    return {
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    }


app.run('dinkedpawn.com', 4311)

# app = web.Application()
# app.router.add_post('/offer', offer)
# web.run_app(app, host='0.0.0.0', port=8898, ssl_context=None)
