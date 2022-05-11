from pprint import pprint
import asyncio
import sys
from PIL import Image
from io import BytesIO

from base64 import b64encode

from signaling import WebsocketSignaling
from live_cam import LiveCam

from webcam_face_detect import RPiFaceDetector, read_known_faces_from_directory

# TODO: Add Graceful Exit

#TODO: Add error handlings: 1- when websocket doesn't connect

def getUID():
    return 2

def getDUID():
    return 1

SOCKET_IO_NAMESPACE = '/live_cam'
SOCKET_IO_SERVER_ADDRESS = f"https://{sys.argv[1]}"

signaling = WebsocketSignaling(SOCKET_IO_SERVER_ADDRESS,
                                   SOCKET_IO_NAMESPACE)

live_cam = LiveCam()
face_detector = RPiFaceDetector("640x480")

current_mode = 'Initialized'

async def switch_modes(mode):
    global current_mode
    print(f"Switching to {mode}")
    if mode == 'Live' and current_mode != 'Live':
            if current_mode == 'Detect':
                face_detector.stop_camera()
            start_live_cam()
    elif mode == 'Detect' and current_mode != 'Detect':
            if current_mode == 'Live':
                await stop_live_cam()
            await start_detector()

def start_live_cam():
    global current_mode
    current_mode = 'Live'
    live_cam.start()

async def stop_live_cam():
    await live_cam.stop()

async def new_webrtc_offer_received(uid: int, d_uid: int, sdp: str, con_type: str):
    if d_uid != getUID():
        pprint("Offer not mine")
        return

    answer_sdp, answer_con_type =\
        await live_cam.answer_connection_offer(sdp, con_type)

    await signaling.send_answer(getUID(), getDUID(), answer_sdp, answer_con_type)

async def start_detector():
    global current_mode
    current_mode = 'Detect'
    # TODO: Add superloop
    print("Face detection starting")

    face_detector.initialize_camera()
    face_detector.start_camera()
    known_faces = read_known_faces_from_directory('./known_faces')
    while current_mode == 'Detect':
        rgb_small_frame = face_detector.capture_frame()
        found_face_locations, found_face_encodings = face_detector.detect_faces(rgb_small_frame)

        # video_bytes_io = BytesIO()
        img_bytes_io = BytesIO()

        img = Image.fromarray(rgb_small_frame)
        img.save(img_bytes_io, format='JPEG')

        found_faces = face_detector.recognize_faces(known_faces,
                                                    found_face_encodings)

        # TODO: Add multiple face detected sending
        if found_faces:
            img_bytes_io.seek(0)
            raw_bytes = img_bytes_io.read(-1)
            b64_encoded_bytes = b64encode(raw_bytes).decode('utf-8')
            face_to_send = found_faces[0]
            footage = {
                'uid': face_to_send.uid,
                'face_encoding': '',
                'isKnown': face_to_send.isKnown,
                'name': face_to_send.name,
                'raw_bytes': b64_encoded_bytes,
                'mimeType': 'image/jpeg'
            }
            await signaling.send('face_detected', footage)
            print("Footage Sent")

        await asyncio.sleep(2)

def stop_detection():
    face_detector.stop_camera()


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

    signaling.add_switch_mode_handler(switch_modes)

    start_live_cam()

    await signaling.connect_and_wait()

if __name__ == "__main__":
    asyncio.run(start_client())

