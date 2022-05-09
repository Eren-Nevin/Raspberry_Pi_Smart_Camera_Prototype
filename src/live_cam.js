import { Signaling } from "./signaling.js";

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

function readDestUID() {
  return 2;
}

const videoElement = document.getElementById("video");
document.getElementById("call-button").addEventListener("click", callPeer);

let signaling = null;
let active_pc = null;
let sent_offer = null;
let data_channel = null;

let localStream = null;

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
  if (sent_offer) {
    console.log("Offer Already Sent");
    return;
  }
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

    console.log("-> Sending offer to remote peer");
    signaling.sendOffer(
      readDestUID(),
      active_pc.localDescription.sdp,
      active_pc.localDescription.type
    );

    sent_offer = new_offer;
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
    iceServers: OPEN_RELAY_SERVERS,
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

  // This is for receiving data channels created by the peer
  // active_pc.addEventListener("datachannel", (ev) => {
  //   data_channel = ev.channel;
  //   data_channel.onmessage = onDataMessage;
  //   data_channel.onopen = onDataMessageOpen;
  //   data_channel.onclose = onDataMessageClose;
  // });

  // This sets that this connection has capacity to receive video
  active_pc.addTransceiver("video", { direction: "recvonly" });
  active_pc.addTransceiver("audio", { direction: "sendrecv" });

  let remoteStream = new MediaStream();

  active_pc.addEventListener("track", (evt) => {
    evt.streams[0].getTracks().forEach((track) => {
      console.log(track);
      remoteStream.addTrack(track);
    });
  });
  videoElement.srcObject = remoteStream;

  console.log("Active PC Created!");
}

function onDataMessage(evt) {
  console.log(`Data Channel: ${evt.data}`);
}

function onDataMessageOpen() {
  console.log(`Data Channel: Open`);
  // TODO: Remove Heartbeat
  setInterval(() => {
    if (data_channel) {
      data_channel.send("Heartbeat");
    }
  }, 5000);
}

function onDataMessageClose() {
  console.log(`Data Channel: Close`);
}

async function callPeer() {
  try {
    if (active_pc !== null) {
      await closeRTCConnection();
      // sent_offer was used to prevent Unwanted offers being sent, now we
      // want to send an offer, so we reset it back to null
      sent_offer = null;
    }
    // await start();
    await createPeerConnection();
    console.log("RTC Connection Created To Offer");

    // TODO: Work on data channel config
    let dataChannelConfig = {};

    // TODO: Do we need certain parameters for data channel?
    data_channel = active_pc.createDataChannel("chat", dataChannelConfig);
    data_channel.onclose = onDataMessageClose;
    data_channel.onopen = onDataMessageOpen;
    data_channel.onmessage = onDataMessage;

    // Adding Microphone

    localStream = await navigator.mediaDevices.getUserMedia({
      video: false,
      audio: true,
    });

    localStream.getTracks().forEach((track) => {
      console.log("Adding mic track");
      active_pc.addTrack(track, localStream);
    });
  } catch (e) {
    console.log(e);
  }
}

async function onAnswerReceived(uid, sdp, con_type) {
  try {
    console.log(`Answer Received From ${uid}`);
    let receivedDescription = new RTCSessionDescription({
      sdp: sdp,
      type: con_type,
    });
    await active_pc.setRemoteDescription(receivedDescription);
  } catch (e) {
    console.log(e);
  }
}

async function closeRTCConnection() {
  try {
    if (data_channel !== null) {
      data_channel.close();
    }
    if (active_pc !== null) {
      await active_pc.close();
    }
  } catch (error) {
    alert(error);
  }
}

async function start() {
  signaling = new Signaling();
  active_pc = null;
  data_channel = null;
  signaling.addConnectionStateChangeHandlers(
    () => {
      console.log("Connected");
    },
    () => {},
    () => {}
  );

  signaling.addNewAnswerHandler(onAnswerReceived);
  signaling.connect();
}

start();
