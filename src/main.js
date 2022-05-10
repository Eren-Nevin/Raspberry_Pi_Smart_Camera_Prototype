import { Signaling } from "./signaling.js";
import { callPeer, onAnswerReceived, initialize } from "./live_cam.js";
import { onFootageReceived } from './sent_footage.js';

const detectButton = document.getElementById('detect-button')
const callButton = document.getElementById("call-button")

callButton.addEventListener("click", async () => {
    switchMode('Live')
    // Hacky way to make sure the client is ready for call
    await new Promise(r => {setTimeout(r, 2000)})
    callPeer()
});

detectButton.addEventListener('click', () => {
    switchMode('Detect')
})

let signaling = null;

function readDestUID() {
  return 2;
}

function sendRTCOffer(sdp, type) {
  signaling.sendOffer(readDestUID(), sdp, type);
}

function switchMode(mode){
    signaling.switchMode(mode)
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
  initialize(sendRTCOffer);

// For sent_footage
    signaling.addSentFootageHandler(onFootageReceived)
    


  signaling.connect();
}

start();
