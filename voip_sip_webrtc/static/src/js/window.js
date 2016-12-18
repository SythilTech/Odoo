odoo.define('voip_sip_webrtc.voip_call_window', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var Model = require('web.DataModel');
var session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var bus = require('bus.bus').bus;
var Notification = require('web.notification').Notification;
var WebClient = require('web.WebClient');

var _t = core._t;
var qweb = core.qweb;


var localStream;
var localVideo = document.querySelector('#localVideo');
var remoteVideo = document.querySelector('#remoteVideo');
var remoteStream = "";
var uuid = uuid();

//var serverConnection;
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

if (navigator.getUserMedia) {
    navigator.getUserMedia({audio: true, video: true}, getUserMediaSuccess, getUserMediaError);
}

function getUserMediaSuccess(stream) {
    console.log("Got Camera Access");

    $.ajax({
	    method: "GET",
		url: "/voip/call/connect",
		data: { call_id: $('#call_id').val() },
            success: function(data) {

        }
    });

    localStream = stream;
	localVideo.src = window.URL.createObjectURL(stream);

    window.peerConnection = new RTCPeerConnection(peerConnectionConfig);
    window.peerConnection.onicecandidate = gotIceCandidate;
    window.peerConnection.ontrack = gotRemoteStream;
    window.peerConnection.addStream(localStream);

    //serverConnection = new WebSocket('ws://' + window.location.hostname + ':8045/');
    //serverConnection.onopen = gotConnectionFromServer;
    //serverConnection.onmessage = gotMessageFromServer;
    //serverConnection.onerror = gotConectionErrorFromServer;
}

function getUserMediaError(error) {
    alert("Failed to access to camera");
};

$( "#voip_start_call" ).click(function() {

    console.log("Call Start: " + uuid);

    window.peerConnection.createOffer().then(createdDescription).catch(errorHandler);

});

function createdDescription(description) {
    console.log('createdDescription: ' + description);

    window.peerConnection.setLocalDescription(description).then(function() {
        //serverConnection.send(JSON.stringify({'sdp': peerConnection.localDescription, 'uuid': uuid}));

        $.ajax({
	        method: "GET",
	    	url: "/voip/call/sdp",
	    	data: { call_id: $('#call_id').val(), sdp: JSON.stringify({'sdp': peerConnection.localDescription}) },
            success: function(data) {

            }
        });

    }).catch(errorHandler);
}

function gotIceCandidate(event) {
    if(event.candidate != null) {
		console.log("Got Ice Candidate: " + event.candidate);
        //serverConnection.send(JSON.stringify({'ice': event.candidate, 'uuid': uuid}));
        $.ajax({
	        method: "GET",
	    	url: "/voip/call/ice",
	    	data: { call_id: $('#call_id').val(), ice: JSON.stringify({'ice': event.candidate}) },
            success: function(data) {

            }
        });
    }
}

function gotRemoteStream(event) {
    console.log("Got Remote Stream: " + event.streams[0]);
    remoteVideo.srcObject = event.streams[0];
    remoteStream = event.streams[0];
}

$( "#voip_end_call" ).click(function() {
    console.log("Call End");
    $.ajax({
	    method: "GET",
		url: "/voip/call/end",
		data: { call_id: $('#call_id').val() },
        success: function(data) {

        }
    });

    //localVideo.src = "";
    localStream.getAudioTracks()[0].stop();
    localStream.getVideoTracks()[0].stop();
    remoteVideo.srcObject = localStream;
    remoteStream.getAudioTracks()[0].enabled = false;
    remoteStream.getAudioTracks()[0].stop();
    remoteStream.getVideoTracks()[0].stop();

});

function uuid() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
  }

  return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
}


WebClient.include({

    show_application: function() {

        bus.on('notification', this, function (notifications) {
            _.each(notifications, (function (notification) {
                if(notification[0][1] === 'voip.join') {

                    //Recreate the div content based on the client side javascript client list
					$("#join-list").empty();
					for (var i = 0; i < clientList.length; i++) {

                        //Update the users state now that they have accepted media access
						if (clientList[i].client_name == notification[1].client_name) {
							clientList[i].state = "media_access";
						}

						var voip_client = clientList[i];

					    $("#join-list").append(voip_client.client_name + " " + voip_client.state + "<br/>");
				    }

					console.log(notification[1].client_name + " Joined the call");
				} else if(notification[0][1] === 'voip.sdp') {
                    var sdp_json = notification[1].sdp;
                    var sdp = JSON.parse(sdp_json)['sdp'];
                    console.log("Got SDP");
                    console.log(sdp_json);

                    window.peerConnection.setRemoteDescription(new RTCSessionDescription(sdp)).then(function() {
						console.log("Set Remote Description");
                        // Only create answers in response to offers
                        if(sdp.type == 'offer') {
							console.log("Create Answer");
                            window.peerConnection.createAnswer().then(createdDescription).catch(errorHandler);
                        }
                    }).catch(errorHandler);

				} else if(notification[0][1] === 'voip.ice') {
                    var ice_json = notification[1].ice;
                    var ice = JSON.parse(ice_json)['ice'];
                    console.log("Got ICE");
                    console.log(ice_json);
					peerConnection.addIceCandidate(new RTCIceCandidate(ice)).catch(errorHandler);
				}

				}

				).bind(this));

        });
        return this._super.apply(this, arguments);
    },

});

});









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

