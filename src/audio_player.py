import asyncio
from logging import currentframe
from pprint import pprint
import threading
from aiortc.mediastreams import MediaStreamTrack
from aiortc.contrib.media import MediaRecorder, MediaRecorderContext
import av
import sounddevice as sd
import soundfile as sf
import numpy as np

# TODO: Fix this inheritance
class RawAudioRecorder(MediaRecorder):

    def __init__(self, file, format=None, options={}):
        super().__init__(file, format, options)

    def addTrack(self, track):
        """
        Add a track to be recorded.

        :param track: A :class:`aiortc.MediaStreamTrack`.
        """

        stream = super().__container.add_stream('pcm_s16le')
        super().__tracks[track] = MediaRecorderContext(stream)

# An attempt to play av.AudioFrames directly. Currently doesn't work
# class AudioPlayer:

#     def __init__(self):
#         self.current_frame = 0
#         self.frames = np.array([[0]], dtype='int16')
#         sd.default.channels = None, 1
#         sd.default.latency = 'low', 'low'
#         sd.default.dtype = 'int16', 'int16'
#         sd.default.samplerate = 48000

#     def addTrack(self, track: MediaStreamTrack):
#         self.track = track

#     async def start(self):
#         m_task = asyncio.create_task(self.read_track())
#         await asyncio.sleep(3)
#         p_task = asyncio.create_task(self.play())
#         # p_task = asyncio.create_task(self.play_recorded())


#     def callback(self, outdata, frames, time, status):
#         print("Callback called")
#         pprint(frames)
#         pprint(len(self.frames))
#         if status:
#             print(status)
        
#         # chunksize = 0
#         # while chunksize < frames:
#         #     chunksize = min(len(self.frames) - self.current_frame, frames)
#         #     asyncio.sleep(0.1)
#         # chunksize = min(len(self.frames) - self.current_frame, frames)
#         # pprint(chunksize)
#         outdata[:] = self.frames[self.current_frame:self.current_frame +
#                                       frames]
#         # if chunksize < frames:
#         #     outdata[chunksize:] = 0
#         #     raise sd.CallbackStop()
#         self.current_frame += frames

#     async def play_recorded(self):
#         sd.play(self.frames, samplerate=48000, blocking=True)
#         sd.wait()



#     async def read_track(self):
#         while True:
#             frame = await self.track.recv()
#             raw_frame_data_array = frame.to_ndarray()

#             # TODO: Make it stereo
#             first_channel = raw_frame_data_array.T[::2]

#             self.frames = np.concatenate([self.frames, first_channel])

#     # This never completes
#     async def play(self):
#         stream = sd.OutputStream(samplerate=48000, callback = self.callback,
#                                  blocksize=48000)
#         stream.start()

# You should only use raw audio containers like wav or alsa as format

