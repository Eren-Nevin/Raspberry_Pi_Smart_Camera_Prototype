import { Signaling } from "./signaling.js";
import {
  callPeer,
  onAnswerReceived,
  initializeLiveCam,
  stopLiveCam,
} from "./live_cam.js";
import {
  initializeFootage,
  stopFootage,
  onFootageReceived,
} from "./sent_footage.js";

const detectButton = document.getElementById("detect-button");
const callButton = document.getElementById("call-button");

let current_mode = "Initialized";

callButton.addEventListener("click", async () => {
  switchMode("Live");
  // Hacky way to make sure the client is ready for call
  await new Promise((r) => {
    setTimeout(r, 2000);
  });
  callPeer();
});

detectButton.addEventListener("click", () => {
  switchMode("Detect");
});

let signaling = null;

function readDestUID() {
  return 2;
}

function sendRTCOffer(sdp, type) {
  signaling.sendOffer(readDestUID(), sdp, type);
}

async function switchMode(mode) {
  if (current_mode === mode) {
    return;
  }
  if (current_mode === "Live") {
    await stopLiveCam();
  } else if (current_mode === "Detect") {
    stopFootage();
  }
    current_mode = mode

    if (mode === 'Live'){
        initializeLiveCam(sendRTCOffer)
    } else if (mode === 'Detect') {
        initializeFootage()
    }
  signaling.switchMode(mode);
}

// function onFaceDetected(

async function start() {
  signaling = new Signaling();
  signaling.addConnectionStateChangeHandlers(
    () => {
      console.log("Connected");
    },
    () => {},
    () => {}
  );

  // For live_cam
  signaling.addNewAnswerHandler(onAnswerReceived);

  // For sent_footage
  signaling.addSentFootageHandler(onFootageReceived);

  signaling.connect();
}

start();

initializeLiveCam(sendRTCOffer);
current_mode = "Live";
