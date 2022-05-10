let socket = null;

const SIGNALING_SERVER_ADDRESS = "dinkedpawn.com:4311";
const SIGNALING_SERVER_SOCKETIO_NAMESPACE = "live_cam";

function readUID() {
  return 1;
}

class OfferOrAnswer {
  uid;
  d_uid;
  sdp;
  con_type;

  constructor(uid, d_uid, sdp, con_type) {
    this.uid = uid;
    this.d_uid = d_uid;
    this.sdp = sdp;
    this.con_type = con_type;
  }
}

class IceCandidate {
  uid;
  d_uid;
  candidate;
  con_type;
  constructor(uid, d_uid, candidate, con_type) {
    this.uid = uid;
    this.d_uid = d_uid;
    this.candidate = candidate;
    this.con_type = con_type;
  }
}

class Footage {
  face;
  media;
  constructor(face, media) {
    this.face = face;
    this.media = media;
  }
}

class Face {
  uid;
  faceEncoding;
  isKnown;
  name;
  constructor(uid, faceEncoding, isKnown, name = "") {
    this.uid = uid;
    this.faceEncoding = faceEncoding;
    this.isKnown = isKnown;
    if (name) {
      this.name = name;
    } else {
      this.name = "Unknown";
    }
  }
}

class FootageMedia {
  arrayBuffer;
  mimeType;
  constructor(arrayBuffer, mimeType) {
    this.arrayBuffer = arrayBuffer;
    this.mimeType = mimeType;
  }
}

// function getSignalingServerAddress() {
//   return "dinkedpawn.com:4311";
// }

class SignalingBase {
  sio;
  serverAddress;
  namespace;

  constructor(server_address, namespace) {
    this.serverAddress = server_address;
    this.namespace = namespace;
    this.sio = io(`${this.serverAddress}/${this.namespace}`, {
      transports: ["websocket"],
      autoConnect: false,
    });
  }

  addConnectionStateChangeHandlers(onConnect, onConnectErrror, onDisconnect) {
    this.sio.on("connect", onConnect);
    this.sio.on("connect_error", onConnectErrror);
    this.sio.on("disconnect", onDisconnect);
  }

  addTopicHandler(topic, onMessage) {
    this.sio.on(topic, onMessage);
  }

  connect() {
    this.sio.connect();
  }

  disconnect() {
    this.sio.disconnect();
  }

  // Note the message should be serialized before sending it or it gets
  // deserialized as a json
  send(topic, message) {
    this.sio.emit(topic, message);
  }
}

class Signaling extends SignalingBase {
  constructor(
    serverAddress = SIGNALING_SERVER_ADDRESS,
    namespace = SIGNALING_SERVER_SOCKETIO_NAMESPACE
  ) {
    super(serverAddress, namespace);
  }

  // For live_cam
  addNewAnswerHandler(onAnswerReceived) {
    const newAnswerHandler = async (answerJson) => {
      const answer = new OfferOrAnswer(
        answerJson["uid"],
        answerJson["d_uid"],
        answerJson["sdp"],
        answerJson["con_type"]
      );

      if (answer.d_uid !== readUID()) {
        console.log("Answer is not for this device");
      }

      await onAnswerReceived(answer.uid, answer.sdp, answer.con_type);
    };
    this.addTopicHandler("new_answer", newAnswerHandler);
  }

  sendOffer(d_uid, sdp, con_type) {
    let offer = new OfferOrAnswer(readUID(), d_uid, sdp, con_type);
    this.send("offer", offer);
  }

  // For sent_footage

  addSentFootageHandler(onFootageReceived) {
    const newFootageHandler = async (footageJson) => {
      console.log(footageJson);

      const face = new Face(
        footageJson["uid"],
        footageJson["face_encoding"],
        footageJson["isKnown"],
        footageJson["name"]
      );
        

      const rawFootageData = convertB64ToUint8Array(footageJson['raw_bytes'])

      const media = new FootageMedia(
        rawFootageData,
        footageJson["mimeType"]
      );

      const footage = new Footage(face, media);

      console.log(footage);

      onFootageReceived(footage);
    };
    this.addTopicHandler("new_face_detected", newFootageHandler);
  }

  switchMode(mode) {
    this.send("switch_mode", mode);
  }
}

function convertB64ToUint8Array(b64String){
      const rawFootageData = Uint8Array.from(
        atob(b64String),
        (c) => c.charCodeAt(0)
      );
    return rawFootageData
}

export { Signaling };
