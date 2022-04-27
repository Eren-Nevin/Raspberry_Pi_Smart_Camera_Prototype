from pprint import pprint
import json
from dataclasses import dataclass, asdict
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.signaling import candidate_from_sdp, candidate_to_sdp
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer
import socketio
import time
import sys
# from socketio import namespace

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




async def createRTCConnection():
    global pc
    global data_channel

    rtc_server = RTCIceServer('stun:stun.l.google.com:19302')
    rtc_config = RTCConfiguration([rtc_server])
    pc = RTCPeerConnection(rtc_config)

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("Data Channel Is Open?")
        print(channel)

        channel.send("Hello")

        @channel.on("message")
        def on_message(message):
            pprint(f"Data Message: {message}")
            # if isinstance(message, str) and message.startswith("ping"):
            #     channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        pprint(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
        elif pc.connectionState == 'connected':
            print("Connected !!!!!")

    @pc.on("iceconnectionstatechange")
    async def on_ice_connection_state_change():
        pprint(f"Ice Connection State is {pc.iceConnectionState}")

    @pc.on("icegatheringstatechange")
    async def on_ice_gathering_state_change():
        pprint(f"Ice Gathering State is {pc.iceGatheringState}")
        if pc.iceGatheringState == 'complete':
            candidates = pc.sctp.transport.transport.iceGatherer.getLocalCandidates()
            print(len(candidates))
            # for m_candidate in candidates:
            #     candidate = IceCandidate(getUID(), getDUID(),
            #                              candidate_to_sdp(m_candidate),
            #                              'new_ice_candidate')
            #     await sio.emit('new_ice_candidate', asdict(candidate),
            #                    namespace=SOCKET_IO_NAMESPACE)

    @pc.on("signalingstatechange")
    async def on_ice_gathering_state_change():
        pprint(f"Signaling State is {pc.signalingState}")

    print("Active PC Created")


async def start_client():
    await createRTCConnection()

    await sio.connect(f"{SOCKET_IO_SERVER_ADDRESS}",
                namespaces=[SOCKET_IO_NAMESPACE], transports=["websocket"])

    await sio.wait()

async def newIceCandidateReceived(message):
    candidate = message
    # if int(candidate['d_uid']) != getUID():
    #     return

    # my_candidate = candidate_from_sdp(candidate['candidate']['candidate'])
    # my_candidate.sdpMid = candidate['candidate']['sdpMid']
    # my_candidate.sdpMLineIndex = candidate['candidate']['sdpMLineIndex']
    # await pc.addIceCandidate(my_candidate)


async def newOfferReceived(message):
    offer = message
    # pprint(f"Offer is: {offer}")
    if int(offer['d_uid']) != getUID():
        pprint("Offer not mine")
        return
    # Check for presence of keys

    # print(received_offer_sdp)

    offerSDP = RTCSessionDescription(sdp=offer['sdp'], type=offer['con_type'])

    # pc_id = f"PeerConnection{uuid.uuid4()}"
    # pcs.add(pc)

    pprint("Created RTC Connection")
    # PLAYER GOES HERE


    # handle offer
    await pc.setRemoteDescription(offerSDP)

    # send answer
    answer = await pc.createAnswer()
    if not answer:
        return

    await pc.setLocalDescription(answer)

    # await sio.emit('new_ice_candidate', asdict(candidate), namespace=SOCKET_IO_NAMESPACE)
    my_answer = OfferOrAnswer(getUID(), getDUID(), pc.localDescription.sdp,
                              pc.localDescription.type)
    # pprint(f"My Answer is {my_answer}")

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
        # pprint(message)
        await newOfferReceived(message)

    @sio.on('new_ice_candidate', namespace=SOCKET_IO_NAMESPACE)
    async def on_new_ice_candidate(message):
        pprint(message)
        await newIceCandidateReceived(message)

    if __name__ == "__main__":
        asyncio.run(start_client())

except Exception as e:
    print(e)

