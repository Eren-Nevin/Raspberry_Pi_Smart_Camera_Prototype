from picamera import PiCamera
from time import sleep

picamera.start_preview()
sleep(5)
picamera.capture('hello.jpg')
camera.stop_preview()
