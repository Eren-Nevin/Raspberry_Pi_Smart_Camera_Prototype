from pprint import pprint
import subprocess
import platform
from subprocess import Popen

from aiortc.contrib.media import  MediaPlayer, MediaRelay
from aiortc.contrib.media import MediaRecorder

from rtc_client import RTCClient

# TODO: Add safe close

class LiveCam:

    def __init__(self,
                 use_mic = True,
                 use_native_audio_playing = False,
                 speaker_audio_format = 'wav',
                 use_speaker = True,
                 use_cam = True,
                 video_resolution = "640x480"):
        self.use_mic = use_mic
        self.use_speaker = use_speaker
        self.use_cam = use_cam
        self.video_resolution = video_resolution
        self.use_data_channel = False
        self.speaker_audio_format = speaker_audio_format
        self.use_native_audio_playing = use_native_audio_playing
        self.state = 'created'

    def is_running(self):
        if self.state == 'started':
            return True
        return False

    def start(self):
        self._start_speaker_player_process()
        self._setup_rtc_client()
        self._create_media_streams()
        self._setup_rtc_tracks()
        self.state = 'started'

    # BUG: if browser is rapidly refereshed (~<5 seconds) several times and
    # calls each time, after third or fourth call, it sigaborts. I think its a
    # problem with not freeing or double freeing the rtc_client
    async def stop(self):
        # TODO: Does termination kill the process?
        self.external_media_player_process.terminate()
        self.external_media_player_process.wait()
        self.video_stream.stop()
        self.camera.video.stop()
        self.mic_stream.stop()
        await self.rtc.stop()
        self.state = 'stopped'
        print("Live Cam Stopped")


    async def answer_connection_offer(self, sdp: str, con_type: str):
        print("New Offer Received")
        answer_sdp, answer_con_type =\
                await self.rtc.answer_connection_offer(sdp, con_type)
        return answer_sdp, answer_con_type

    # Currently we can't play audio frames directly, if we could, we change this to
    # True and thus not need to create MediaRecorder object and ffplay process
    # Its so important to have nobuffer and low_delay flags for low latency playback
    def _start_speaker_player_process(self):
        if not self.use_native_audio_playing:
            external_media_player_cmd = ['ffplay', '-fflags', 'nobuffer',
                                         '-flags', 'low_delay',
                                         '-i', '-', '-f', self.speaker_audio_format,
                                         '-acodec','pcm_s16le'
                                         ]
            # IMPORTANT: Remember that ffplay needs to find a dispaly to run, otherwise
            # it pauses asking: Could not initialize SDL - No available video device
            # This means before turning on the camera, you need to plug an hdmi to it
            # for now.
            # TODO: Make ffplay doesn't pause for display
            self.external_media_player_process = Popen(external_media_player_cmd,
                                                  stdin=subprocess.PIPE,
                                                  stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.DEVNULL,
                                                  )


    def _setup_rtc_client(self):
        rtc = RTCClient()
        rtc.start()
        pc = rtc.get_peer_connection()

        def on_ice_connection_state_change():
            pprint(f"Ice Connection State is {pc.iceConnectionState}")
        def on_ice_gathering_state_change():
            pprint(f"Ice Gathering State is {pc.iceGatheringState}")

        rtc.add_ice_handlers(on_ice_connection_state_change,
                             on_ice_gathering_state_change)

        def on_signaling_state_change():
            pprint(f"Signaling State is {pc.signalingState}")

        rtc.add_signal_state_change_handler(on_signaling_state_change)

        async def on_connectionstatechange():
            pprint(f"Connection state is {pc.connectionState}")
            # TODO: Add other connection states
            if pc.connectionState == 'failed':
                self.external_media_player_process.terminate()
                self.external_media_player_process.wait()
                self.state = 'failed'
                # self.video_stream.stop()
                # self.camera.video.stop()
                # self.mic_stream.stop()
                # await pc.close()
                #TODO: On stop, stop everything including camera, mic and
                # speakers
                # if use_speaker and recorder:
                #     recorder.stop()

        rtc.add_connection_state_change_handler(on_connectionstatechange)

        def on_data_channel_open(channel):
            print("Data channel openned")
            with open('video.mp4', 'rb') as footage:
                footage_bytes = footage.read(-1)
                self.rtc.send_data_to_channel(footage_bytes)

        def on_data_channel_message(message):
            print(message)

        rtc.add_data_channel_handler(on_data_channel_open,
                                     on_data_channel_message)

        self.rtc = rtc

    # We can use the picamera module to create a recording based on our specific
    # needs and stream it somehow (e.g. socket, BytesIO, ...) to MediaPlayer class.
    # Currently, since we're behind schedule, we are reading directly from source
    # device.
    # Note that the buffered=False is the reason we can stream virtually lag free
    def _create_camera_video_stream_track(self, resolution: str):
        options = {"framerate": "30", "video_size": resolution, 'input_format':
                   'h264', 'vcodec': 'copy'}
        if platform.system() == "Darwin":
            self.camera = MediaPlayer(
                "default:none", format="avfoundation", options=options
            )
        elif platform.system() == "Windows":
            self.camera = MediaPlayer(
                "video=Integrated Camera", format="dshow", options=options
            )
        else:
            self.camera = MediaPlayer("/dev/video0", format="v4l2", options=options)
        # webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
        relay = MediaRelay()
        return relay.subscribe(self.camera.video, buffered=False)

    # Capture camera mic to create a media track
    def _create_microphone_media_stream_track(self):
        player = MediaPlayer("default", format="pulse")
        return player.audio
        # TODO: Do we need relay to decrease latency?
        # relay = MediaRelay()
        # return relay.subscribe(player.audio, buffered=False)

    def _create_media_streams(self):
        self.video_stream =\
            self._create_camera_video_stream_track(self.video_resolution)

        self.mic_stream = self._create_microphone_media_stream_track()


    def _setup_rtc_tracks(self):
        # Send camera video
        if self.use_cam:
            self.video_sender = self.rtc.add_track(self.video_stream)

        # Send Mic
        if self.use_mic:
            self.mic_sender = self.rtc.add_track(self.mic_stream)

        async def on_received_track(track):
            pprint(track.kind)
            if not self.use_speaker:
                return

            # Refer to use_native_audio_playing. 
            if self.use_native_audio_playing:
                pass
                # audio_player = AudioPlayer()
                # audio_player.addTrack(track)
                # await audio_player.start()

            else:
                # TODO: Use the inheritance version after it works
                # recorder = RawAudioRecorder(external_media_player_process.stdin,
                #                          format=audio_format,
                #                          )
                recorder = MediaRecorder(self.external_media_player_process.stdin,
                                         format=self.speaker_audio_format,
                                         )
                recorder.addTrack(track)
                await recorder.start()

        self.rtc.add_on_new_track_received(on_received_track)
