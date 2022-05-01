let videoElement = document.getElementById("video");

let socket = null;
let active_pc = null;
let data_channel = null;

const STUN_SERVERS = ["stun:stun.l.google.com:19302"];
const OPEN_RELAY_SERVERS = [
    {
      urls: "stun:openrelay.metered.ca:80",
    },
    {
      urls: "turn:openrelay.metered.ca:80",
      username: "openrelayproject",
      credential: "openrelayproject",
    },
    {
      urls: "turn:openrelay.metered.ca:443",
      username: "openrelayproject",
      credential: "openrelayproject",
    },
    {
      urls: "turn:openrelay.metered.ca:443?transport=tcp",
      username: "openrelayproject",
      credential: "openrelayproject",
    },
  ];

const SIGNALING_SERVER_SOCKETIO_NAMESPACE = "live_cam";

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

function getSignalingServerAddress() {
  return "dinkedpawn.com:4311";
}

function readUID() {
  return 1;
}

function readDestUID() {
  return 2;
}

function createSocketIO() {
  serverAddress = getSignalingServerAddress();
  socket = io(`${serverAddress}/${SIGNALING_SERVER_SOCKETIO_NAMESPACE}`, {
    transports: ["websocket"],
    autoConnect: false,
  });
}

function connectSocket() {
  socket.connect();
}

function setSocketEventListeners() {
  socket.on("connect", () => {
    console.log("Connected To Websocket");
  });

  socket.on("new_answer", async (message) => {
    // console.log(message);
    await newAnswerReceived(message);
  });

  // Refer to the newIceCandidateReceived function for the reason
  // socket.on("new_ice_candidate", async (message) => {
  //   await newIceCandidateReceived(message);
  // });

  // Refer to the newOfferReceived function for the reason
  // socket.on("new_offer", async (message) => {
  //   await newOfferReceived(message);
  // });
}

// This is here to cancel ice trickling by waiting for all candidates to be
// gathered before creating the offer. We're doing this because aiortc doesn't
// support ice trickling for now
async function waitForIceGathering() {
  let promise = new Promise(function (resolve) {
    if (active_pc.iceGatheringState === "complete") {
      resolve();
    } else {
      function checkState() {
        if (active_pc.iceGatheringState === "complete") {
          active_pc.removeEventListener("icegatheringstatechange", checkState);
          resolve();
        }
      }
      active_pc.addEventListener("icegatheringstatechange", checkState);
    }
  });

  await promise;
  return;
}
async function handleNegotiationNeededEvent() {
  console.log("Negotiation Needed");
  try {
    let new_offer = await active_pc.createOffer();
    if (active_pc.signalingState != "stable") {
      console.log("     -- The connection isn't stable yet; postponing...");
      return;
    }

    console.log("---> Setting local description to the offer");
    await active_pc.setLocalDescription(new_offer);

    // Waiting for all ice candidates to arrive so that our local description
    // contains them all meaning no new ice candidate would be found after our
    // initial offer. This is for disabling ice trickling.
    await waitForIceGathering();

    let offer = new OfferOrAnswer(
      readUID(),
      readDestUID(),
      active_pc.localDescription.sdp,
      active_pc.localDescription.type
    );

    // document.getElementById("offer-sdp").textContent = offer.sdp;

    console.log("-> Sending offer to remote peer");
    socket.emit("offer", offer);
  } catch (error) {
    console.log("Error in Negotiation Handling");
    console.log(error);
  }
}

// Since we won't use trickling, we won't need to send candidates as soon as we
// find them. Realistically we won't need to listen for them at all but we're
// just using this handler to log the found candidates
function handleICECandidateEvent(event) {
  if (event.candidate) {
    console.log("*** Outgoing ICE candidate: " + event.candidate.candidate);
  }
}

function handleICEConnectionStateChangeEvent(event) {
  console.log(
    "*** ICE connection state changed to " + active_pc.iceConnectionState
  );
}

function handleSignalingStateChangeEvent(event) {
  console.log(
    "*** WebRTC signaling state changed to: " + active_pc.signalingState
  );
}

function handleICEGatheringStateChangeEvent(event) {
  console.log(
    "*** ICE gathering state changed to: " + active_pc.iceGatheringState
  );
}

async function createPeerConnection() {
  let config = {
    iceServers: OPEN_RELAY_SERVERS
  };

  config.iceServers = [{ urls: STUN_SERVERS }];

  active_pc = new RTCPeerConnection(config);
  active_pc.addEventListener("negotiationneeded", handleNegotiationNeededEvent);
  active_pc.addEventListener("icecandidate", handleICECandidateEvent);
  active_pc.addEventListener(
    "iceconnectionstatechange",
    handleICEConnectionStateChangeEvent
  );
  active_pc.addEventListener(
    "icegatheringstatechange",
    handleICEGatheringStateChangeEvent
  );
  active_pc.addEventListener(
    "signalingstatechange",
    handleSignalingStateChangeEvent
  );
  active_pc.addEventListener("datachannel", (ev) => {
    data_channel = ev.channel;
    data_channel.onmessage = onDataMessage;
    data_channel.onopen = onDataMessageOpen;
    data_channel.onclose = onDataMessageClose;
  });

  // This sets that this connection has capacity to receive video
  active_pc.addTransceiver("video", { direction: "recvonly" });
  active_pc.addTransceiver("audio", { direction: "sendrecv" });

// active_pc.addTrack()
    //

    let remoteStream = new MediaStream();

  active_pc.addEventListener("track", (evt) => {
      evt.streams[0].getTracks().forEach(track => {
          console.log(track)
          remoteStream.addTrack(track)
      })
  });
    videoElement.srcObject = remoteStream

  console.log("Active PC Created!");
}

function onDataMessage(evt) {
  console.log(`Data Channel: ${evt.data}`);
}

function onDataMessageOpen() {
  console.log(`Data Channel: Open`);
}

function onDataMessageClose() {
  console.log(`Data Channel: Close`);
}

async function callPeer() {
  try {
    await start();
    await createPeerConnection();
    console.log("RTC Connection Created To Offer");

    let dataChannelConfig = {};

    // TODO: Do we need certain parameters for data channel?
    dc = active_pc.createDataChannel("chat", dataChannelConfig);
    dc.onclose = onDataMessageClose;
    dc.onopen = onDataMessageOpen;
    dc.onmessage = onDataMessage;
  } catch (e) {
    console.log(e);
  }
}

async function newAnswerReceived(answerJson) {
  try {
    let answer = new OfferOrAnswer(
      answerJson["uid"],
      answerJson["d_uid"],
      answerJson["sdp"],
      answerJson["con_type"]
    );

    if (answer.d_uid == readUID()) {
      // TODO: Do we need to create this object or the answer itself was
      // sufficient
      let receivedDescription = new RTCSessionDescription({
        sdp: answer.sdp,
        type: answer.con_type,
      });
      // document.getElementById("answer-sdp").textContent = answer.sdp;
      await active_pc.setRemoteDescription(receivedDescription);
    }
  } catch (e) {
    console.log(e);
  }
}

async function closeRTCConnection() {
  try {
    if (data_channel) {
      data_channel.close();
    }
    if (active_pc) {
      await active.close();
    }
  } catch (error) {
    alert(error);
  }
}

async function start() {
  socket = null;
  active_pc = null;
  data_channel = null;
  createSocketIO();
  setSocketEventListeners();
  connectSocket();
  // await createPeerConnection()
}
