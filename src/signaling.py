from types import FunctionType
from typing import Coroutine, Dict
import socketio
from dataclasses import dataclass, asdict

ANSWER_TOPIC = 'answer'
OFFER_TOPIC = 'new_offer'

@dataclass
class OfferOrAnswer:
    uid: int
    d_uid: int
    sdp: str
    con_type: str

@dataclass
class IceCandidate:
    uid: int
    d_uid: int
    candidate: str
    con_type: str

class WebsocketSignalingBase:
    def __init__(self, server_address: str, namespace: str):
        self.server_address = server_address
        self.namespace = namespace
        self.sio = socketio.AsyncClient(ssl_verify=False)

    def add_connections_state_change_handlers(self, on_connect, on_connect_error,
                                              on_disconnect):
        self.sio.on('connect', on_connect, self.namespace)
        self.sio.on('connect_error', on_connect_error, self.namespace)
        self.sio.on('disconnect', on_disconnect, self.namespace)

    def add_handler(self, topic:str, on_message):
        self.sio.on(topic, on_message, self.namespace)

    async def connect_and_wait(self):
        await self.sio.connect(f"{self.server_address}",
                    namespaces=[self.namespace], transports=["websocket"])
        await self.sio.wait()

    async def send(self, topic: str, data):
        await self.sio.emit(topic, data, namespace=self.namespace)


class WebsocketSignaling(WebsocketSignalingBase):
    def __init__(self, server_address: str, namespace: str):
        super().__init__(server_address, namespace)

    async def send_answer(self, uid: int, duid: int, sdp: str, con_type: str):
        my_answer = OfferOrAnswer(uid, duid, sdp, con_type)
        await self.send(ANSWER_TOPIC, asdict(my_answer))


    def add_new_offer_handler(self, on_new_offer):
        async def offer_handler(offer):
            await on_new_offer(int(offer['uid']),
                               int(offer['d_uid']),
                               offer['sdp'],
                               offer['con_type'])

        self.add_handler(OFFER_TOPIC, offer_handler)
