from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamTrack
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer
from aiortc.contrib.media import  MediaPlayer, MediaRelay
from aiortc.contrib.media import MediaRecorder

from typing import List, Optional, Tuple

class RTCClient:
    GOOGLE_ICE_SERVER = RTCIceServer('stun:stun.l.google.com:19302')
    OPEN_RELAY_ICE_SERVER = RTCIceServer('stun:openrelay.metered.ca:80')
    OPEN_RELAY_TURN_SERVER_1 = RTCIceServer('turn:openrelay.metered.ca:80',
                                            username='openrelayproject',
                                            credential='openrelayproject')
    OPEN_RELAY_TURN_SERVER_2 = RTCIceServer('turn:openrelay.metered.ca:443',
                                            username='openrelayproject',
                                            credential='openrelayproject')
    OPEN_RELAY_TURN_SERVER_3 = RTCIceServer('turn:openrelay.metered.ca:443?transport=tcp',
                                            username='openrelayproject',
                                            credential='openrelayproject')
    def __init__(self,
                 ice_turn_servers: List[RTCIceServer] = [GOOGLE_ICE_SERVER],
                 rtc_config: Optional[RTCConfiguration] = None):
        if rtc_config:
            config = rtc_config
        else:
            config = RTCConfiguration(ice_turn_servers)

        self.pc = RTCPeerConnection(config)


    def get_peer_connection(self):
        return self.pc

    # Note that the handler is triggered once the data channel is opened and it
    # has access to a single parameter 'channel' which is the channel object.
    # You can use this channel object to send or listen on messages. For
    # example:
    # channel.send("Hello")
    # @channel.on("message")
    # def on_message(message):
    #     pprint(f"Data Message: {message}")
    def add_data_channel_handler(self, on_open):
        self.pc.on("datachannel", on_open)


    # Examples of handlers
    # async def on_ice_connection_state_change():
    #     pprint(f"Ice Connection State is {self.pc.iceConnectionState}")
    # async def on_ice_gathering_state_change():
    #     pprint(f"Ice Gathering State is {self.pc.iceGatheringState}")
    def add_ice_handlers(self, on_ice_connection_state_change,
                         on_ice_gathering_state_change):
        self.pc.on("iceconnectionstatechange", on_ice_connection_state_change)
        self.pc.on("icegatheringstatechange", on_ice_gathering_state_change)

    # Example of handler
    #async def on_connectionstatechange():
    #    pprint(f"Connection state is {self.pc.connectionState}")
    #    if self.pc.connectionState == "failed":
    #        if self.pc:
    #            await self.pc.close()
    #            #TODO: On stop, stop everything including camera, mic and
    #            # speakers
    #            # if use_speaker and recorder:
    #            #     recorder.stop()
    def add_connection_state_change_handler(self, on_connection_state_change):
        self.pc.on("connectionstatechange", on_connection_state_change)


    # Example of handler
    # async def on_ice_gathering_state_change():
    #     pprint(f"Signaling State is {self.pc.signalingState}")
    def add_signal_state_change_handler(self, on_signal_state_change):
        self.pc.on("signalingstatechange", on_signal_state_change)


    # Note that this handler is called with a single argument 'track'. Example:
    # async def onTrack(track):
    #     pprint(track.kind)
    #     if not use_speaker:
    #         return

    #     # Refer to use_native_audio_playing. 
    #     if use_native_audio_playing:
    #         pass
    #         # audio_player = AudioPlayer()
    #         # audio_player.addTrack(track)
    #         # await audio_player.start()

    #     else:
    #         # TODO: Use the inheritance version after it works
    #         # recorder = RawAudioRecorder(external_media_player_process.stdin,
    #         #                          format=audio_format,
    #         #                          )
    #         recorder = MediaRecorder(external_media_player_process.stdin,
    #                                  format=audio_format,
    #                                  )
    #         recorder.addTrack(track)
    #         await recorder.start()
    def add_on_new_track_received(self, on_new_track_received):
        self.pc.on("track", on_new_track_received)


    def add_track(self, track: MediaStreamTrack):
        return self.pc.addTrack(track)

    # It taks sdp and connection type of offer as strings and returns the same
    # for answer
    async def answer_connection_offer(self, sdp:str, con_type:str) \
        -> Tuple[str, str]:
        print("Creating SDP")
        offerSDP = RTCSessionDescription(sdp=sdp, type=con_type)
        # handle offer
        await self.pc.setRemoteDescription(offerSDP)
        # create answer
        answer = await self.pc.createAnswer()
        if not answer:
            return '', ''
        await self.pc.setLocalDescription(answer)

        return self.pc.localDescription.sdp, self.pc.localDescription.type
