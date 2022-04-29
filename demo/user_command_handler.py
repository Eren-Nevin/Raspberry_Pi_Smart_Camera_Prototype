from pathlib import PosixPath
from pyrogram import Client, filters
from pyrogram.types.messages_and_media.message import Message
from webcam_face_detect import VideoFaceDetector, Face, KnownFace, read_known_faces_from_directory
import cv2
import asyncio

from time import time

# from camera import rpi_cam
# my_camera = rpi_cam.Camera()

# def handle_command(user_query: str, client: Client, message: Message):
#     if user_query == 'start':
#         my_camera.start();

#     elif user_query == 'capture':
#         my_camera.capture_still_to_local_file(PosixPath('current.jpg'))
#         res = client.send_photo(message.chat.id, 'current.jpg')

#     elif user_query == 'stop':
#         my_camera.stop();

# found_one = False

async def start(client: Client, message: Message):
    known_faces = read_known_faces_from_directory('./known_faces')
    video_face_detector = VideoFaceDetector()
    while True:
        frame, rgb_small_frame = video_face_detector.capture_frame()
        t1 = time()
        found_face_locations, found_face_encodings =\
            video_face_detector.detect_faces(rgb_small_frame)
        t2 = time()
        found_faces = video_face_detector.recognize_faces(known_faces,
                                                          found_face_encodings)
        t3 = time()
        for face in found_faces:
            # await client.send_message(message.chat.id, f"{face.name} Seen")
            # frame_photo = cv2.imencode('.jpg', frame)[1]
            face.name = face.name if face.isKnown else "Unknown"
            cv2.imwrite(f"pic.jpg", frame)
            await client.send_photo(message.chat.id, "pic.jpg",
                                    caption=face.name)

        t4 = time()
        print(f"{t2-t1} for detection, {t3 - t2} for recognition, {t4 - t3} for\
              sending")
        await asyncio.sleep(3)




async def handle_command(user_query: str, client: Client, message: Message):
    if user_query == 'start':
        await start(client, message)
        # my_camera.start();
        pass

    elif user_query == 'capture':
        # my_camera.capture_still_to_local_file(PosixPath('current.jpg'))
        # res = client.send_photo(message.chat.id, 'current.jpg')
        pass

    elif user_query == 'stop':
        # my_camera.stop();
        pass
