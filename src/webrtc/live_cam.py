from pprint import pprint
from dataclasses import dataclass, asdict
import asyncio
import sys

import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer, MediaRelay
# from aiortc.contrib.signaling import candidate_from_sdp, candidate_to_sdp

def getUID():
    return 2

def getDUID():
    return 1

@dataclass
class OfferOrAnswer:
    uid: int
    d_uid: int
    sdp: str
    con_type: str

@dataclass
class IceCandidate:
    uid: int
    d_uid: int
    candidate: str
    con_type: str

SOCKET_IO_NAMESPACE = '/live_cam'

SOCKET_IO_SERVER_ADDRESS = f"http://{sys.argv[1]}"

sio = socketio.AsyncClient()

# We can use the picamera module to create a recording based on our specific
# needs and stream it somehow (e.g. socket, BytesIO, ...) to MediaPlayer class.
# Currently, since we're behind schedule, we are reading directly from source
# device.
# Note that the buffered=False is the reason we can stream virtually lag free
def create_media_stream_track():
    options = {"framerate": "30", "video_size": "1280x720"}
    webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
    relay = MediaRelay()
    return relay.subscribe(webcam.video, buffered=False)

async def createRTCConnection():
    global pc
    global data_channel

    rtc_server = RTCIceServer('stun:stun.l.google.com:19302')
    rtc_config = RTCConfiguration([rtc_server])
    pc = RTCPeerConnection(rtc_config)

    
    # TODO: Do we need to force codec?

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("Data Channel Is Open?")
        print(channel)

        channel.send("Hello")

        @channel.on("message")
        def on_message(message):
            pprint(f"Data Message: {message}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        pprint(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()

    @pc.on("iceconnectionstatechange")
    async def on_ice_connection_state_change():
        pprint(f"Ice Connection State is {pc.iceConnectionState}")

    @pc.on("icegatheringstatechange")
    async def on_ice_gathering_state_change():
        pprint(f"Ice Gathering State is {pc.iceGatheringState}")

    @pc.on("signalingstatechange")
    async def on_ice_gathering_state_change():
        pprint(f"Signaling State is {pc.signalingState}")

    print("Active PC Created")


async def start_client():
    await createRTCConnection()

    await sio.connect(f"{SOCKET_IO_SERVER_ADDRESS}",
                namespaces=[SOCKET_IO_NAMESPACE], transports=["websocket"])

    await sio.wait()

async def newOfferReceived(message):
    offer = message
    if int(offer['d_uid']) != getUID():
        pprint("Offer not mine")
        return

    video_sender = pc.addTrack(create_media_stream_track())

    # codecs = RTCRtpSender.getCapabilities('video').codecs
    # pprint(codecs)
    # pprint(pc.getTransceivers())


    print("Creating SDP")
    offerSDP = RTCSessionDescription(sdp=offer['sdp'], type=offer['con_type'])

    pprint("Created RTC Connection")
    # PLAYER GOES HERE


    # handle offer
    await pc.setRemoteDescription(offerSDP)

    # send answer
    answer = await pc.createAnswer()
    if not answer:
        return

    await pc.setLocalDescription(answer)

    my_answer = OfferOrAnswer(getUID(), getDUID(), pc.localDescription.sdp,
                              pc.localDescription.type)

    await sio.emit('answer', asdict(my_answer), namespace=SOCKET_IO_NAMESPACE)


try:
    @sio.event(namespace=SOCKET_IO_NAMESPACE)
    def connect():
        print("I'm connected!")

    @sio.event(namespace=SOCKET_IO_NAMESPACE)
    def connect_error(data):
        print(data)
        print("The connection failed!")

    @sio.event(namespace=SOCKET_IO_NAMESPACE)
    def disconnect():
        print("I'm disconnected!")

    @sio.on('new_offer', namespace=SOCKET_IO_NAMESPACE)
    async def on_new_offer(message):
        await newOfferReceived(message)

    if __name__ == "__main__":
        asyncio.run(start_client())

except Exception as e:
    print(e)

