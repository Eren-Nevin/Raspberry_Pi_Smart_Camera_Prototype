from pprint import pprint
import asyncio
import sys
from PIL import Image
from io import BytesIO


from signaling import WebsocketSignaling
from live_cam import LiveCam

from webcam_face_detect import RPiFaceDetector, read_known_faces_from_directory

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

    if live_cam.is_running():
        await live_cam.stop()

    live_cam.start()

    # if pc:
    #     await pc.close()
    #     webcam.video.stop()
    if d_uid != getUID():
        pprint("Offer not mine")
        return

    answer_sdp, answer_con_type =\
        await live_cam.answer_connection_offer(sdp, con_type)

    await signaling.send_answer(getUID(), getDUID(), answer_sdp, answer_con_type)

    # await asyncio.sleep(10)

    # await live_cam.stop()

    # face_detector = RPiFaceDetector("640x480")
    # face_detector.start_camera()
    # rgb_small_frame = face_detector.capture_frame()
    # found_face_locations, found_face_encodings = face_detector.detect_faces(rgb_small_frame)

    # known_faces = read_known_faces_from_directory('./known_faces')

    # # video_bytes_io = BytesIO()
    # # img_bytes_io = BytesIO()
    # # img = Image.fromarray(rgb_small_frame)
    # # img.save("pic.jpg")

    # found_faces = face_detector.recognize_faces(known_faces,
    #                                             found_face_encodings)
     
    # print(found_faces[0].name)


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

