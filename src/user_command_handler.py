from pathlib import PosixPath
from pyrogram import Client, filters
from pyrogram.types.messages_and_media.message import Message
from camera import rpi_cam

my_camera = rpi_cam.Camera()

def handle_command(user_query: str, client: Client, message: Message):
    if user_query == 'start':
        my_camera.start();

    elif user_query == 'capture':
        my_camera.capture_still_to_local_file(PosixPath('current.jpg'))
        res = client.send_photo(message.chat.id, 'current.jpg')

    elif user_query == 'stop':
        my_camera.stop();
