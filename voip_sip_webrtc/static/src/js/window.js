var localStream;
var localVideo = document.querySelector('#localVideo');
var remoteVideo = document.querySelector('#remoteVideo');

var peerConnection;
var serverConnection;
var peerConnectionConfig = {'iceServers': [{'urls': 'stun:stun.services.mozilla.com'}, {'urls': 'stun:stun.l.google.com:19302'}]};

navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
window.RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
window.RTCIceCandidate = window.RTCIceCandidate || window.mozRTCIceCandidate || window.webkitRTCIceCandidate;
window.RTCSessionDescription = window.RTCSessionDescription || window.mozRTCSessionDescription || window.webkitRTCSessionDescription;

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
    console.log("Call Start");
    peerConnection = new RTCPeerConnection(peerConnectionConfig);
    peerConnection.onicecandidate = gotIceCandidate;
    peerConnection.onatrack = gotRemoteStream;
    peerConnection.addStream(localStream);
    if(isCaller) {
        peerConnection.createOffer(gotDescription, createOfferError);
    }
}

function gotDescription(description) {
    console.log('Got Description: ' + description);
    peerConnection.setLocalDescription(description, function () {
        serverConnection.send(JSON.stringify({'sdp': description}));
    }, function() {console.log('Set Description Error')});
}

function gotIceCandidate(event) {
	console.log("Got Ice Candidate: " + event.candidate);
    if(event.candidate != null) {
        serverConnection.send(JSON.stringify({'ice': event.candidate}));
    }
}

function gotRemoteStream(event) {
    console.log("Got Remote Stream");
    remoteVideo.src = window.URL.createObjectURL(event.stream);
}

function createOfferError(error) {
    console.log("Create Offer Error: " + error);
}

//--------------Connection based functions-------------------

function gotConnectionFromServer() {
    console.log("Web Socket Contection Successful");
}

function gotMessageFromServer(message) {
    if(!peerConnection) start(false);

    console.log(message.data);

    var signal = JSON.parse(message.data);
    if(signal.sdp) {
        peerConnection.setRemoteDescription(new RTCSessionDescription(signal.sdp), function() {
            peerConnection.createAnswer(gotDescription, createAnswerError);
        }, function(error) {
            alert("failed to set remote description: " + error);
        }
        );
    } else if(signal.ice) {
        peerConnection.addIceCandidate(new RTCIceCandidate(signal.ice));
    }
}

function createAnswerError(error) {
    console.log("Create Answer Error: " + error);
}

function gotConectionErrorFromServer(error) {
	console.log(error);
}
