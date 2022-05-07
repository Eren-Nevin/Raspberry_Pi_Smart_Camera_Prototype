from pprint import pprint
from dataclasses import dataclass, asdict
import asyncio
import subprocess
import sys
import platform
from aiortc.mediastreams import MediaStreamTrack

import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.media import MediaRecorder
# from aiortc.contrib.signaling import candidate_from_sdp, candidate_to_sdp
from aiortc.rtcrtpreceiver import RemoteStreamTrack


from subprocess import Popen

# Currently doesn't work
from audio_player import RawAudioRecorder

use_data_channel = False
use_mic = True
use_speaker = True
audio_format = 'wav'

video_resolution = "640x480"

# Currently we can't play audio frames directly, if we could, we change this to
# True and thus not need to create MediaRecorder object and ffplay process
use_native_audio_playing = False


# Its so important to have nobuffer and low_delay flags for low latency playback
if not use_native_audio_playing:
    external_media_player_cmd = ['ffplay', '-fflags', 'nobuffer',
                                 '-flags', 'low_delay',
                                 '-i', '-', '-f', audio_format,
                                 '-acodec','pcm_s16le'
                                 ]
    external_media_player_process = Popen(external_media_player_cmd,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)

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

# SOCKET_IO_SERVER_ADDRESS = f"http://{sys.argv[1]}"
SOCKET_IO_SERVER_ADDRESS = f"https://{sys.argv[1]}"


sio = socketio.AsyncClient(ssl_verify=False)
pc = None

# We can use the picamera module to create a recording based on our specific
# needs and stream it somehow (e.g. socket, BytesIO, ...) to MediaPlayer class.
# Currently, since we're behind schedule, we are reading directly from source
# device.
# Note that the buffered=False is the reason we can stream virtually lag free
def create_media_stream_track(resolution: str):
    global webcam
    options = {"framerate": "30", "video_size": resolution, 'input_format':
               'h264', 'vcodec': 'copy'}
    if platform.system() == "Darwin":
        webcam = MediaPlayer(
            "default:none", format="avfoundation", options=options
        )
    elif platform.system() == "Windows":
        webcam = MediaPlayer(
            "video=Integrated Camera", format="dshow", options=options
        )
    else:
        webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
    # webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
    relay = MediaRelay()
    return relay.subscribe(webcam.video, buffered=False)

# Capture camera mic to create a media track
def create_microphone_media_stream_track():
    player = MediaPlayer("default", format="pulse")
    return player.audio


async def createRTCConnection():
    global pc
    global data_channel
    global recorder

    google_rtc_server = RTCIceServer('stun:stun.l.google.com:19302')
    google_rtc_config = RTCConfiguration([google_rtc_server])

    open_relay_rtc_server = RTCIceServer('stun:openrelay.metered.ca:80')
    open_relay_turn_server_1 = RTCIceServer('turn:openrelay.metered.ca:80',
                                            username='openrelayproject',
                                            credential='openrelayproject')
    open_relay_turn_server_2 = RTCIceServer('turn:openrelay.metered.ca:443',
                                            username='openrelayproject',
                                            credential='openrelayproject')
    open_relay_turn_server_3 = RTCIceServer('turn:openrelay.metered.ca:443?transport=tcp',
                                            username='openrelayproject',
                                            credential='openrelayproject')
    rtc_open_relay_config = RTCConfiguration([open_relay_rtc_server,
                                              open_relay_turn_server_1,
                                              open_relay_turn_server_2,
                                              open_relay_turn_server_3,
                                              ])

    pc = RTCPeerConnection(google_rtc_config)
    # pc = RTCPeerConnection(rtc_open_relay_config)

    # TODO: Do we need to force codec?

    @pc.on("datachannel")
    def on_datachannel(channel):
        if not use_data_channel:
            return
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
            if pc:
                await pc.close()
                #TODO: Fix recorder is not defined
                if use_speaker and recorder:
                    recorder.stop()

    @pc.on("iceconnectionstatechange")
    async def on_ice_connection_state_change():
        pprint(f"Ice Connection State is {pc.iceConnectionState}")

    @pc.on("icegatheringstatechange")
    async def on_ice_gathering_state_change():
        pprint(f"Ice Gathering State is {pc.iceGatheringState}")

    @pc.on("signalingstatechange")
    async def on_ice_gathering_state_change():
        pprint(f"Signaling State is {pc.signalingState}")


    # Receive Mic
    @pc.on("track")
    async def onTrack(track):
        pprint(track.kind)
        if not use_speaker:
            return

        # Refer to use_native_audio_playing. 
        if use_native_audio_playing:
            pass
            # audio_player = AudioPlayer()
            # audio_player.addTrack(track)
            # await audio_player.start()

        else:
            # TODO: Use the inheritance version after it works
            # recorder = RawAudioRecorder(external_media_player_process.stdin,
            #                          format=audio_format,
            #                          )
            recorder = MediaRecorder(external_media_player_process.stdin,
                                     format=audio_format,
                                     )
            recorder.addTrack(track)
            await recorder.start()

    print("Active PC Created")


async def start_client():
    await sio.connect(f"{SOCKET_IO_SERVER_ADDRESS}",
                namespaces=[SOCKET_IO_NAMESPACE], transports=["websocket"])

    await sio.wait()

async def newOfferReceived(message):
    print("New Offer Received")
    # if pc:
    #     await pc.close()
    #     webcam.video.stop()
    await createRTCConnection()
    offer = message
    if int(offer['d_uid']) != getUID():
        pprint("Offer not mine")
        return


    # Send camera video
    video_sender = pc.addTrack(create_media_stream_track(video_resolution))


    # Send Mic
    if use_mic:
        audio_sender = pc.addTrack(create_microphone_media_stream_track())


    print("Creating SDP")
    offerSDP = RTCSessionDescription(sdp=offer['sdp'], type=offer['con_type'])

    pprint("Created RTC Connection")

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
