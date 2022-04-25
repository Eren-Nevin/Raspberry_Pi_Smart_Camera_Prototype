var dataChannelLog = document.getElementById("data-channel"),
  iceConnectionLog = document.getElementById("ice-connection-state"),
  iceGatheringLog = document.getElementById("ice-gathering-state"),
  signalingLog = document.getElementById("signaling-state");
uidTextBox = document.getElementById("uid");
destUidTextBox = document.getElementById("destination_uid");
callButton = document.getElementById("call-button");

let socket = null;

const STUN_SERVERS = ["stun:stun.l.google.com:19302"];

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
  constructor(uid, d_uid, candidate, con_type) {
    this.uid = uid;
    this.d_uid = d_uid;
    this.candidate = candidate;
    this.con_type = con_type;
  }
}

var active_pc = null;
let pc_used_for_call = null;
let pc_used_for_answer = null;

function readUID() {
  return uidTextBox.value;
}

function readDestUID() {
  return destUidTextBox.value;
}

function createSocketIO() {
  socket = io(`dinkedpawn.com:4311/my_namespace`, {
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

  socket.on("new_offer", async (message) => {
    console.log(message);
    await newOfferReceived(message);
  });

  socket.on("new_answer", async (message) => {
    console.log(message);
    await newAnswerReceived(message);
  });

  socket.on("new_ice_candidate", async (message) => {
    console.log(message);
    await newIceCandidateReceived(message);
  });
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

    let offer = new OfferOrAnswer(
      readUID(),
      readDestUID(),
      active_pc.localDescription.sdp,
      active_pc.localDescription.type
    );

    document.getElementById("offer-sdp").textContent = offer.sdp;

    console.log("-> Sending offer to remote peer");
    socket.emit("offer", offer);
  } catch (error) {
    console.log("Error in Negotiation Handling");
    console.log(error);
  }
}

function handleICECandidateEvent(event) {
  if (event.candidate) {
    console.log("*** Outgoing ICE candidate: " + event.candidate.candidate);

    created_ice_candidate = new IceCandidate(
      readUID(),
      readDestUID(),
      event.candidate,
      "new_ice_candidate"
    );

    socket.emit("new_ice_candidate", created_ice_candidate);
  }
}

function handleICEConnectionStateChangeEvent(event) {
  console.log(
    "*** ICE connection state changed to " + active_pc.iceConnectionState
  );
  iceConnectionLog.textContent += " -> " + active_pc.iceConnectionState;

  // switch(active_pc.iceConnectionState) {
  //   case "closed":
  //   case "failed":
  //   case "disconnected":
  //     closeVideoCall();
  //     break;
  // }
}

function handleSignalingStateChangeEvent(event) {
  console.log(
    "*** WebRTC signaling state changed to: " + active_pc.signalingState
  );
  signalingLog.textContent += " -> " + active_pc.signalingState;
}

function handleICEGatheringStateChangeEvent(event) {
  console.log(
    "*** ICE gathering state changed to: " + active_pc.iceGatheringState
  );
  iceGatheringLog.textContent += " -> " + active_pc.iceGatheringState;
}

async function createPeerConnection() {
  let config = {};

  if (document.getElementById("use-stun").checked) {
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
    receiveChannel = ev.channel;
      receiveChannel.onmessage = (evt) => {
            dataChannelLog.textContent += "< " + evt.data + "\n";
          receiveChannel.send("Pong")
      }
    receiveChannel.onopen = onDataMessageOpen
    receiveChannel.onclose = onDataMessageClose
  });
  console.log("Active PC Created!");
}

function onDataMessage(evt){
    dataChannelLog.textContent += "< " + evt.data + "\n";
    // if (evt.data === 'Ping'){
    //     evt.channel.send("Pong")
    // }
    // if (evt.data.substring(0, 4) === "pong") {
    //   var elapsed_ms =
    //     current_stamp() - parseInt(evt.data.substring(5), 10);
    //   dataChannelLog.textContent += " RTT " + elapsed_ms + " ms\n";

}

function onDataMessageOpen(){
    dataChannelLog.textContent += "- open\n";
    // dcInterval = setInterval(function () {
    //   var message = "ping " + current_stamp();
    //   dataChannelLog.textContent += "> " + message + "\n";
    //   dc.send(message);
    // }, 1000);
}

function onDataMessageClose(){
    // clearInterval(dcInterval);
    dataChannelLog.textContent += "- close\n";
}

async function callPeer() {
  try {
    await createPeerConnection();
    console.log("RTC Connection Created To Offer");

    if (document.getElementById("use-datachannel").checked) {
      var parameters = JSON.parse(
        document.getElementById("datachannel-parameters").value
      );

      dc = active_pc.createDataChannel("chat", parameters);
      dc.onclose = function () {
        clearInterval(dcInterval);
        dataChannelLog.textContent += "- close\n";
      };
      dc.onopen = function () {
        dataChannelLog.textContent += "- open\n";
        dcInterval = setInterval(function () {
          dc.send("Ping");
        }, 1000);
      };
      dc.onmessage = function (evt) {
        dataChannelLog.textContent += "< " + evt.data + "\n";

        if (evt.data.substring(0, 4) === "pong") {
          var elapsed_ms =
            current_stamp() - parseInt(evt.data.substring(5), 10);
          dataChannelLog.textContent += " RTT " + elapsed_ms + " ms\n";
        }
      };
    }

    // return await pc
  } catch (e) {
    console.log(e);
  }
}

async function newOfferReceived(offerJson) {
  try {
    let offer = new OfferOrAnswer(
      offerJson["uid"],
      offerJson["d_uid"],
      offerJson["sdp"],
      offerJson["con_type"]
    );

    console.log("Offer is:");
    console.log(offer);
    // The call is for us
    if (offer.d_uid === readUID()) {
      // if (!active_pc){
      await createPeerConnection();
      // }
      document.getElementById("offer-sdp").textContent = offer.sdp;
      console.log(`OFFER IS FOR ME ${readUID()}`);
      // TODO: Do we need to create this object or the answer itself was
      // sufficient
      let receivedDescription = new RTCSessionDescription({
        sdp: offer.sdp,
        type: offer.con_type,
      });
      await active_pc.setRemoteDescription(receivedDescription);
      answer = await active_pc.createAnswer();
      await active_pc.setLocalDescription(answer);
      let my_answer = new OfferOrAnswer(
        readUID(),
        readDestUID(),
        answer.sdp,
        answer.type
      );
      console.log("My Answer is");
      console.log(my_answer);
      socket.emit("answer", my_answer);
    }
  } catch (error) {
    console.log(error);
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
      document.getElementById("answer-sdp").textContent = answer.sdp;
      await active_pc.setRemoteDescription(receivedDescription);
    }
  } catch (e) {
    console.log(e);
  }
}

async function newIceCandidateReceived(iceCandidateJson) {
  try {
    let candidate = new IceCandidate(
      iceCandidateJson["uid"],
      iceCandidateJson["d_uid"],
      iceCandidateJson["candidate"],
      iceCandidateJson["con_type"]
    );

    if (candidate.d_uid == readUID()) {
      // TODO: Do we need to create this object or the answer itself was
      // sufficient

      let receivedCandidate = new RTCIceCandidate(candidate.candidate);
      await active_pc.addIceCandidate(receivedCandidate);
      // document.getElementById("answer-sdp").textContent = answer.sdp;
      // await active_pc.setRemoteDescription(receivedDescription);
    }
  } catch (e) {
    console.log(e);
  }
}

async function closeRTCConnection(pc, dc) {
  try {
    if (dc) {
      dc.close();
    }
    await pc.close();
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

start();
