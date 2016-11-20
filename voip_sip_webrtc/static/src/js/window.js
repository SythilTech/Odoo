var localStream;
var pc1;
var pc2;
var offerOptions = {
  offerToReceiveAudio: 1,
  offerToReceiveVideo: 1
};

function gotRemoteStream(e) {
  document.querySelector('#other_video').srcObject = e.stream;
  console.log('pc2 received remote stream');
}

function getName(pc) {
  return (pc === pc1) ? 'pc1' : 'pc2';
}

function onAddIceCandidateSuccess(pc) {
  console.log(getName(pc) + ' addIceCandidate success');
}

function onSetRemoteSuccess(pc) {
  console.log(getName(pc) + ' setRemoteDescription complete');
}

function getOtherPc(pc) {
  return (pc === pc1) ? pc2 : pc1;
}

function onIceStateChange(pc, event) {
  if (pc) {
    console.log(getName(pc) + ' ICE state: ' + pc.iceConnectionState);
    console.log('ICE state change event: ', event);
  }
}

function onIceCandidate(pc, event) {
  if (event.candidate) {
    getOtherPc(pc).addIceCandidate(
      new RTCIceCandidate(event.candidate)
    ).then(
      function() {
        onAddIceCandidateSuccess(pc);
      },
      function(err) {
        onAddIceCandidateError(pc, err);
      }
    );
    console.log(getName(pc) + ' ICE candidate: \n' + event.candidate.candidate);
  }
}

function onSetLocalSuccess(pc) {
  console.log(getName(pc) + ' setLocalDescription complete');
}

function onCreateAnswerSuccess(desc) {
  console.log('Answer from pc2:\n' + desc.sdp);
  console.log('pc2 setLocalDescription start');
  pc2.setLocalDescription(desc).then(
    function() {
      onSetLocalSuccess(pc2);
    },
    onSetSessionDescriptionError
  );
  console.log('pc1 setRemoteDescription start');
  pc1.setRemoteDescription(desc).then(
    function() {
      onSetRemoteSuccess(pc1);
    },
    onSetSessionDescriptionError
  );
}

function onSetSessionDescriptionError(error) {
  console.log('Failed to set session description: ' + error.toString());
}

function onCreateSessionDescriptionError(error) {
  console.log('Failed to create session description: ' + error.toString());
}

function onCreateOfferSuccess(desc) {
  console.log('Offer from pc1\n' + desc.sdp);
  console.log('pc1 setLocalDescription start');
  pc1.setLocalDescription(desc).then(
    function() {
      onSetLocalSuccess(pc1);
    },
    onSetSessionDescriptionError
  );
  console.log('pc2 setRemoteDescription start');
  pc2.setRemoteDescription(desc).then(
    function() {
      onSetRemoteSuccess(pc2);
    },
    onSetSessionDescriptionError
  );
  console.log('pc2 createAnswer start');
  // Since the 'remote' side has no media stream we need
  // to pass in the right constraints in order for it to
  // accept the incoming offer of audio and video.
  pc2.createAnswer().then(
    onCreateAnswerSuccess,
    onCreateSessionDescriptionError
  );
}

function call() {
    alert("Call Start");

    var servers = null;
    pc1 = new RTCPeerConnection(servers);
    console.log('Created local peer connection object pc1');

    pc1 = new RTCPeerConnection(servers);
    console.log('Created local peer connection object pc1');
    pc1.onicecandidate = function(e) {
        onIceCandidate(pc1, e);
    };

    pc2 = new RTCPeerConnection(servers);
    console.log('Created remote peer connection object pc2');

    pc2.onicecandidate = function(e) {
        onIceCandidate(pc2, e);
    };

    pc1.oniceconnectionstatechange = function(e) {
        onIceStateChange(pc1, e);
    };

    pc2.oniceconnectionstatechange = function(e) {
        onIceStateChange(pc2, e);
    };

    pc2.onaddstream = gotRemoteStream;

    pc1.addStream(localStream);
    console.log('Added local stream to pc1');

    console.log('pc1 createOffer start');
    pc1.createOffer(
        offerOptions
    ).then(
        onCreateOfferSuccess,
        onCreateSessionDescriptionError
    );

}