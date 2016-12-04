var localStream;
var localVideo = document.querySelector('#localVideo');
var remoteVideo = document.querySelector('#remoteVideo');
var uuid;

var peerConnection;
var serverConnection;
var peerConnectionConfig = {
    'iceServers': [
        {'urls': 'stun:stun.services.mozilla.com'},
        {'urls': 'stun:stun.l.google.com:19302'},
    ]
};

navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
window.RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
window.RTCIceCandidate = window.RTCIceCandidate || window.mozRTCIceCandidate || window.webkitRTCIceCandidate;
window.RTCSessionDescription = window.RTCSessionDescription || window.mozRTCSessionDescription || window.webkitRTCSessionDescription;
uuid = uuid();

if (navigator.getUserMedia) {
    navigator.getUserMedia({audio: true, video: true}, getUserMediaSuccess, getUserMediaError);
}

function getUserMediaSuccess(stream) {
    console.log("Got Camera Access");
    localStream = stream;
	localVideo.src = window.URL.createObjectURL(stream);
    //serverConnection = new WebSocket('ws://192.168.56.101:8045/');
    serverConnection = new WebSocket('ws://' + window.location.hostname + ':8045/');
    serverConnection.onopen = gotConnectionFromServer;
    serverConnection.onmessage = gotMessageFromServer;
    serverConnection.onerror = gotConectionErrorFromServer;
}

function getUserMediaError(error) {
    alert("Failed to access to camera");
};

function end_call() {
    $.ajax({
	    method: "GET",
		url: "/voip/call/end",
		data: { call_id: $('#call_id').val() },
            success: function(data) {

        }
    });

    localVideo.src = "";
    localStream.getAudioTracks()[0].stop();
    localStream.getVideoTracks()[0].stop();
}

function start(isCaller) {
    console.log("Call Start: " + uuid);
    peerConnection = new RTCPeerConnection(peerConnectionConfig);
    peerConnection.onicecandidate = gotIceCandidate;
    peerConnection.ontrack = gotRemoteStream;
    peerConnection.addStream(localStream);
    if(isCaller) {
        peerConnection.createOffer().then(createdDescription).catch(errorHandler);
    }
}

function gotIceCandidate(event) {
    if(event.candidate != null) {
		console.log("Got Ice Candidate: " + event.candidate);
        serverConnection.send(JSON.stringify({'ice': event.candidate, 'uuid': uuid}));
    }
}

function gotRemoteStream(event) {
    console.log("Got Remote Stream: " + event.streams[0]);
    remoteVideo.srcObject = event.streams[0];
}

function createOfferError(error) {
    console.log("Create Offer Error: " + error);
}

//--------------Connection based functions-------------------

function gotConnectionFromServer() {
    console.log("Web Socket Contection Successful");
}

function errorHandler(error) {
    console.log(error);
}

function createdDescription(description) {
    console.log('createdDescription: ' + description);

    peerConnection.setLocalDescription(description).then(function() {
        serverConnection.send(JSON.stringify({'sdp': peerConnection.localDescription, 'uuid': uuid}));
    }).catch(errorHandler);
}

function gotMessageFromServer(message) {
    if(!peerConnection) start(false);

    var signal = JSON.parse(message.data);
console.log(signal.sdp);
    // Ignore messages from ourself
    console.log("uuid: " + signal.uuid);
    if(signal.uuid == uuid) return;

    if(signal.sdp) {
		console.log("Got SDP");
        peerConnection.setRemoteDescription(new RTCSessionDescription(signal.sdp)).then(function() {
            // Only create answers in response to offers
            if(signal.sdp.type == 'offer') {
                peerConnection.createAnswer().then(createdDescription).catch(errorHandler);
            }
        }).catch(errorHandler);
    } else if(signal.ice) {
        peerConnection.addIceCandidate(new RTCIceCandidate(signal.ice)).catch(errorHandler);
    }
}

function createAnswerError(error) {
    console.log("Create Answer Error: " + error);
}

function gotConectionErrorFromServer(error) {
	console.log(error);
}

function uuid() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
  }

  return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
}