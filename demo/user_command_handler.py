import shutil
import subprocess
from uuid import uuid4
from PIL import Image
from io import BytesIO
from pathlib import PosixPath
from pyrogram import Client, filters
from pyrogram.types.messages_and_media.message import Message
from webcam_face_detect import RPiFaceDetector, GeneralFaceDetectorCamera, Face, KnownFace, read_known_faces_from_directory
# from audio_player import say
import pyttsx3
import cv2
import asyncio
import os

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

engine = pyttsx3.init()

known_faces = read_known_faces_from_directory('./known_faces')

# adding_unknown_person = False
# last_unknown_person = None

async def handle_faces_general(client: Client, message: Message):
    known_faces = read_known_faces_from_directory('./known_faces')
    video_face_detector = GeneralFaceDetectorCamera()
    while True:
        frame, rgb_small_frame = video_face_detector.capture_frame()
        found_face_locations, found_face_encodings =\
            video_face_detector.detect_faces(rgb_small_frame)
        found_faces = video_face_detector.recognize_faces(known_faces,
                                                          found_face_encodings)
        for face in found_faces:
            # await client.send_message(message.chat.id, f"{face.name} Seen")
            # frame_photo = cv2.imencode('.jpg', frame)[1]
            face.name = face.name if face.isKnown else "Unknown"
            cv2.imwrite(f"pic.jpg", frame)
            await client.send_photo(message.chat.id, "pic.jpg",
                                    caption=face.name)

        # TODO: Replace it with a sane algorithm that waits until the last face
        # go out of frame and replaced by a new one.
        await asyncio.sleep(3)

async def handle_faces_rpi(client: Client, message: Message):
    i = 0
    video_face_detector = RPiFaceDetector("320x240")
    video_face_detector.setup_buffer(500000)
    video_face_detector.start_video_capture()
    # TODO: Remove this maybe to add parallelism
    while True:
        if os.path.exists('motion.mp4'): os.remove('motion.mp4')
        if os.path.exists('pic.jpg'): os.remove('pic.jpg')
        rgb_small_frame = video_face_detector.capture_frame()
        img_bytes_io = BytesIO()
        # video_bytes_io = BytesIO()
        img = Image.fromarray(rgb_small_frame)
        img.save("pic.jpg")
        # img.save(img_bytes_io, 'JPEG')

        found_face_locations, found_face_encodings =\
            video_face_detector.detect_faces(rgb_small_frame)
        found_faces = video_face_detector.recognize_faces(known_faces,
                                                          found_face_encodings)

        await handle_found_faces(client, message, video_face_detector, found_faces)


        # await asyncio.sleep(1)

# TODO: handle cases where multiple faces are present in the frame at the same
# time
# TODO: Make video bytes_io and use av instead of using ffmpeg command or at
# least make it parallel
async def handle_found_faces(client: Client, message: Message,
                         video_face_detector, found_faces):
    def caption_for_face(face):
        if face.isKnown:
            return f"{face.name} arrived"
        else:
            return "Stranger detected"

    if not found_faces:
        return

    face = found_faces[0]
    video_face_detector.save_captured_video(3, 'motion.h264')
    # TODO: Increase convertion performance using hardware
    convert_h264_to_mp4('motion.h264')
    print("converted Captured video")
    face.name = face.name if face.isKnown else "Unknown"
    engine.say(face.name)
    engine.runAndWait()
    await client.send_video(message.chat.id, 'motion.mp4',
                            caption=caption_for_face(face))

    video_face_detector.clear_video_buffer()
    # This would change after multiple face in frame is implemented


    # if not face.isKnown:
    #     await handle_not_known_face(client, message, face)

    # await client.send_message(message.chat.id, f"{face.name} Seen")
    # frame_photo = cv2.imencode('.jpg', frame)[1]
    # cv2.imwrite(f"pic.jpg", frame)
    # video_face_detector.


# async def handle_not_known_face(client: Client, message: Message, face: Face):
#     global last_unknown_person, adding_unknown_person
#     await client.send_message(message.chat.id, "You can add this person to known \
#     ones by supplying a name")
#     last_unknown_person = face
#     adding_unknown_person = True

# def add_unknown_person(name):
#     global adding_unknown_person
#     global last_unknown_person
#     new_known_face = KnownFace(uuid4().int, last_unknown_person.face_encoding,
#                                name, '')
#     known_faces.append(new_known_face)
#     print(f"Known face added {name}")
#     adding_unknown_person = False
    # last_unknown_person = None



async def start(client: Client, message: Message):
    await handle_faces_rpi(client, message)


def convert_h264_to_mp4(input_file):
    ffmpeg_arg = [
        "ffmpeg", "-r", "30", "-i", input_file, '-vcodec', 'copy',\
        f"./{input_file.split('.')[0]}.mp4"
    ]

    ffmpeg_process = subprocess.Popen(ffmpeg_arg,
                                      stderr=subprocess.DEVNULL,
                                      )

    ffmpeg_process.wait()



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
