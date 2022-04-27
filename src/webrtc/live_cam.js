let signalingServerAddressTextBox = 
    document.getElementById("signaling-server-address");
let uidTextBox = document.getElementById("uid");
let destUidTextBox = document.getElementById("destination_uid");

let socket = null;
let active_pc = null;
let data_channel = null;

const STUN_SERVERS = ["stun:stun.l.google.com:19302"];

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

function getSignalingServerAddress(){
    console.log(signalingServerAddressTextBox.text)
    console.log(signalingServerAddressTextBox.value)
    return signalingServerAddressTextBox.value
}

function readUID() {
  return uidTextBox.value;
}

function readDestUID() {
  return destUidTextBox.value;
}

function createSocketIO() {
    serverAddress = getSignalingServerAddress()
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
async function waitForIceGathering(){
    let promise = new Promise(function(resolve) {
            if (active_pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (active_pc.iceGatheringState === 'complete') {
                        active_pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                active_pc.addEventListener('icegatheringstatechange', checkState);
            }
    })

    await promise
    return

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
    await waitForIceGathering()


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
    iceServers: [
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
    ],
  };

  if (!document.getElementById("use-turn").checked) {
    config.iceServers = [{ urls: STUN_SERVERS }];
  }

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
      await start()
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
  createSocketIO();
  setSocketEventListeners();
  connectSocket();
  // await createPeerConnection()
}

// Here are not needed functions.

// Since the client library we use for camera doesn't support trickle ice, it
// doesn't send its ice candidates progressively but it sends them all at once
// in form of its answer to our offer. This is why we don't need to listen to
// new_ice_candidate events of our signaling system.
// async function newIceCandidateReceived(iceCandidateJson) {
//   try {
//     let candidate = new IceCandidate(
//       iceCandidateJson["uid"],
//       iceCandidateJson["d_uid"],
//       iceCandidateJson["candidate"],
//       iceCandidateJson["con_type"]
//     );

//     // console.log(candidate);

//     if (candidate.d_uid == readUID()) {
//       // TODO: Do we need to create this object or the answer itself was
//       // sufficient


//       let receivedCandidate = new RTCIceCandidate(candidate.candidate);
//       await active_pc.addIceCandidate(receivedCandidate);
//     }
//   } catch (e) {
//     console.log(e);
//   }
// }

// Our current architecture is that the we offer connectio to our camera client.
// This is why we don't need to listen on any new offer received but only on
// answers.
// async function newOfferReceived(offerJson) {
//   try {
//     let offer = new OfferOrAnswer(
//       offerJson["uid"],
//       offerJson["d_uid"],
//       offerJson["sdp"],
//       offerJson["con_type"]
//     );

//     console.log("Offer is:");
//     console.log(offer);
//     // The call is for us
//     if (offer.d_uid === readUID()) {
//       // if (!active_pc){
//       await createPeerConnection();
//       // }
//       // document.getElementById("offer-sdp").textContent = offer.sdp;
//       console.log(`OFFER IS FOR ME ${readUID()}`);
//       // TODO: Do we need to create this object or the answer itself was
//       // sufficient
//       let receivedDescription = new RTCSessionDescription({
//         sdp: offer.sdp,
//         type: offer.con_type,
//       });
//       await active_pc.setRemoteDescription(receivedDescription);
//       answer = await active_pc.createAnswer();
//       await active_pc.setLocalDescription(answer);
//       let my_answer = new OfferOrAnswer(
//         readUID(),
//         readDestUID(),
//         answer.sdp,
//         answer.type
//       );
//       console.log("My Answer is");
//       console.log(my_answer);
//       socket.emit("answer", my_answer);
//     }
//   } catch (error) {
//     console.log(error);
//   }
// }
