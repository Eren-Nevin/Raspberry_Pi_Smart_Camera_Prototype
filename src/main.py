from pprint import pprint
import asyncio
import sys

from signaling import WebsocketSignaling
from live_cam import LiveCam

# TODO: Add Graceful Exit

def getUID():
    return 2

def getDUID():
    return 1

SOCKET_IO_NAMESPACE = '/live_cam'
SOCKET_IO_SERVER_ADDRESS = f"https://{sys.argv[1]}"
signaling = WebsocketSignaling(SOCKET_IO_SERVER_ADDRESS,
                                   SOCKET_IO_NAMESPACE)

live_cam = LiveCam()

async def new_webrtc_offer_received(uid: int, d_uid: int, sdp: str, con_type: str):

    live_cam.setup()

    # if pc:
    #     await pc.close()
    #     webcam.video.stop()
    if d_uid != getUID():
        pprint("Offer not mine")
        return

    answer_sdp, answer_con_type =\
        await live_cam.answer_connection_offer(sdp, con_type)

    await signaling.send_answer(getUID(), getDUID(), answer_sdp, answer_con_type)


async def signaling_on_connect():
    print("I'm Connected")

async def signaling_on_connect_error(message):
    print(f"Error: {message}")
    print("The connection failed!")

async def signaling_on_disconnect():
    print("I'm Disconnected")


async def start_client():

    signaling.add_connections_state_change_handlers(signaling_on_connect,
                                                    signaling_on_connect_error,
                                                    signaling_on_disconnect)

    signaling.add_new_offer_handler(new_webrtc_offer_received)

    await signaling.connect_and_wait()

if __name__ == "__main__":
    asyncio.run(start_client())

