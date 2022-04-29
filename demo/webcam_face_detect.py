from pprint import pprint
import face_recognition
import cv2
import numpy as np

from pathlib import Path

import os

import uuid
from typing import Dict, List

KNOWN_FACES_DIRECTORY_PATH = './known_faces'

class Face:
    def __init__(self, uid: int, face_encoding, isKnown=False):
        self.uid = uid
        self.face_encoding = face_encoding
        self.isKnown = isKnown

class KnownFace(Face):
    def __init__(self, uid: int, face_encoding, name: str, pic_path: str):
        super().__init__(uid, face_encoding, True)
        self.name = name
        self.pic_path = pic_path


def create_known_face(name: str, pic_path: str, encoding=None):
    uid = uuid.uuid4().int
    image = face_recognition.load_image_file(pic_path)
    if encoding:
        face_encoding = encoding
    else:
        face_encoding = face_recognition.face_encodings(image)[0]
    known_face = KnownFace(uid, face_encoding, name, pic_path)
    return known_face

def read_known_faces_from_directory(m_dir=KNOWN_FACES_DIRECTORY_PATH):
    faces = []
    for pic_path in os.listdir(m_dir):
        name = Path(pic_path).name.split('.')[0]
        print(name)
        known_face = create_known_face(name, f"{m_dir}/{pic_path}")
        faces.append(known_face)

    return faces


class VideoFaceDetector:
    def __init__(self):
        # self.process_this_frame = True
        # TODO: Is using picamera better than cv2 on rapsberry pi?
        self.video_capture = cv2.VideoCapture(0)
        pass

    def capture_frame(self):
        # Grab a single frame of video
        ret, frame = self.video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        return frame, rgb_small_frame

    def detect_faces(self, rgb_small_frame):
            found_face_locations = []

            # Find all the faces and face encodings in the current frame of video
            found_face_locations = face_recognition.face_locations(rgb_small_frame)
            found_face_encodings = face_recognition.face_encodings(rgb_small_frame, found_face_locations)

            return found_face_locations, found_face_encodings

    def recognize_faces(self, known_faces, found_face_encodings):
        # found_unknown_faces = []
        # found_known_faces = []
        found_faces = []
        known_face_encodings_list = list(map(lambda face: face.face_encoding, known_faces))

        for face_encoding in found_face_encodings:
            # See if the face is a match for the known face(s)
            matches =\
            face_recognition.compare_faces(known_face_encodings_list,
                                                     face_encoding)


            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances =\
            face_recognition.face_distance(known_face_encodings_list,
                                           face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                found_known_face = known_faces[best_match_index]
                # found_unknown_faces.append(found_known_face)
                found_faces.append(found_known_face)
            else:
                found_unknown_face = Face(uuid.uuid4().int, face_encoding)
                # found_known_faces.append(found_unknown_face)
                found_faces.append(found_unknown_face)

        return found_faces

    # Display the results
    def show_result(self, frame, face_locations, found_faces):

        for (top, right, bottom, left), face in zip(face_locations, found_faces):

            if face.isKnown:
                name = face.name
            else:
                name = "Unknown"

            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Video', frame)


if __name__ == '__main__':
    known_faces = read_known_faces_from_directory()
    videoFaceDetector = VideoFaceDetector()
    process_this_frame = True
    last_found_faces = []
    last_found_face_locations = []
    while True:
        frame, rgb_small_frame = videoFaceDetector.capture_frame()
        if process_this_frame:
            found_face_locations, found_face_encodings =\
            videoFaceDetector.detect_faces(rgb_small_frame)
            found_faces = videoFaceDetector.recognize_faces(known_faces,
                                                            found_face_encodings)
            last_found_face_locations = found_face_locations
            last_found_faces = found_faces

        videoFaceDetector.show_result(frame, last_found_face_locations,
                                      last_found_faces)

        process_this_frame = not process_this_frame
        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    videoFaceDetector.video_capture.release()
    cv2.destroyAllWindows()
