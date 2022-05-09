const footageVideoElement = document.getElementById("footage");

function loadArrayByteAsVideo(arrayBuffer, videoElement){
  const blob = new Blob([arrayBuffer]);
    const file = new File([blob], {type: 'video/mp4'})
    const src = URL.createObjectURL(file)
    videoElement.src = src
    videoElement.load()
    videoElement.play()
}

export default footage_arraybuf

