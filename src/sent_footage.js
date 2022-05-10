const videoElement = document.getElementById("video");
const imageElement = document.getElementById("footage");
const textElement = document.getElementById('footage-name')


function onFootageReceived(footage){
    // TODO: Select based on mimetype
    loadArrayByteAsImage(
        footage.media.arrayBuffer,
        footage.media.mimeType,
        imageElement)
    textElement.textContent = footage.face.name;
    // loadArrayByteAsVideo(
    //     footage.media.arrayBuffer,
    //     footage.media.mimeType,
    //     videoElement
    // )
}

function loadArrayByteAsImage(arrayBuffer, mimeType, imageElement){
  const blob = new Blob([arrayBuffer]);
    const file = new File([blob], {type: mimeType})
    const src = URL.createObjectURL(file)
    imageElement.src = src
}

function loadArrayByteAsVideo(arrayBuffer, mimeType, videoElement){
  const blob = new Blob([arrayBuffer]);
    const file = new File([blob], {type: mimeType})
    const src = URL.createObjectURL(file)
    videoElement.src = src
    videoElement.load()
    videoElement.play()
}

export {onFootageReceived}

