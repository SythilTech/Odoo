odoo.define('voip_sip_webrtc.voip_call_notification', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var rpc = require('web.rpc');
var weContext = require('web_editor.context');
var odoo_session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var bus = require('bus.bus').bus;
var Notification = require('web.notification').Notification;
var WebClient = require('web.WebClient');
var SystrayMenu = require('web.SystrayMenu');

var _t = core._t;
var qweb = core.qweb;

ajax.loadXML('/voip_sip_webrtc/static/src/xml/voip_window.xml', qweb);

var mySound = "";
var countdown;
var secondsLeft;
var callSeconds;
var call_id = "";
var myNotif = "";
var incomingNotification;
var incoming_ring_interval;
var outgoingNotification;
var role;
var mode = false;
var call_type = ""
var to_partner_id;
var outgoing_ring_interval;
var call_interval;
var call_sdp = "";
var ice_candidate_queue = [];
var got_remote_description = false;
var userAgent;
var to_sip;

var peerConnectionConfig = {
    'iceServers': [
        {'urls': 'stun:stun.services.mozilla.com'},
        {'urls': 'stun:stun.l.google.com:19302'},
    ]
};

//navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
window.navigator.mediaDevices.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mediaDevices.getUserMedia || navigator.msGetUserMedia;
window.RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
window.RTCIceCandidate = window.RTCIceCandidate || window.mozRTCIceCandidate || window.webkitRTCIceCandidate;
window.RTCSessionDescription = window.RTCSessionDescription || window.mozRTCSessionDescription || window.webkitRTCSessionDescription;

var localStream;
var localVideo = document.querySelector('#localVideo');
var remoteVideo = document.querySelector('#remoteVideo');
var remoteStream = "";

var VoipCallClient = Widget.extend({
    init: function (p_role, p_mode, p_call_type, p_to_partner_id) {
        this.role = p_role;
        this.mode = p_mode;
        this.call_type = p_call_type;
        this.to_partner_id = p_to_partner_id;

        //temp fix since the rest of the code still uses global variables
        role = p_role;
        mode = p_mode;
        call_type = p_call_type;
        to_partner_id = p_to_partner_id;

    },
    requestMediaAccess: function (contraints) {

        if (navigator.webkitGetUserMedia) {
		    navigator.webkitGetUserMedia(contraints, getUserMediaSuccess, getUserMediaError);
		} else {
            window.navigator.mediaDevices.getUserMedia(contraints).then(getUserMediaSuccess).catch(getUserMediaError);
		}
	},
    endCall: function () {
		console.log("End Call");
	},
});

function getUserMediaSuccess(stream) {
    console.log("Got Media Access");

    $(".s-voip-manager").css("display","block");

    localVideo = document.querySelector('#localVideo');
    remoteVideo = document.querySelector('#remoteVideo');

    localStream = stream;
	localVideo.src = window.URL.createObjectURL(stream);

    window.peerConnection = new RTCPeerConnection(peerConnectionConfig);
    window.peerConnection.onicecandidate = gotIceCandidate;
    //window.peerConnection.ontrack = gotRemoteStream;
    window.peerConnection.onaddstream = gotRemoteStream;
    window.peerConnection.addStream(localStream);

    console.log(role);
    console.log(call_type);

    if (role == "caller") {
		if (call_type == "external") {
		    //Send the sdp now since we need it for the INVITE
		    window.peerConnection.createOffer().then(createCall).catch(errorHandler);
	    } else {

            //Avoid sending the SDP data since it will stuff up the SDP answer
            rpc.query({
		        model: 'voip.server',
		        method: 'voip_call_notify',
		        args: [mode, to_partner_id, call_type, '']
		    }).then(function(result){
                console.log("Notify Callee of incoming phone call");
            });

		}
    }

    if (role == "callee") {
		//Start sending out SDP now since both caller and callee have granted media access
		console.log("Create SDP Offer");
		window.peerConnection.createOffer().then(createdDescription).catch(errorHandler);
	}


}

function getUserMediaError(error) {
    alert("Failed to access to media: " + error);
};



WebClient.include({

    show_application: function() {

        $('body').append(qweb.render('voip_sip_webrtc.VoipWindow', {}));
        $('body').append(qweb.render('voip_sip_webrtc.ChatWindow', {}));

        $(".s-voip-manager").draggable().resizable({handles: 'ne, se, sw, nw'});
        $(".s-chat-manager").draggable().resizable({handles: 'ne, se, sw, nw'});

        bus.on('notification', this, function (notifications) {
            _.each(notifications, (function (notification) {


                  if (notification[0][1] === 'voip.notification') {
					var self = this;

					call_id = notification[1].voip_call_id;

					if (notification[1].direction == 'incoming') {
				    	var from_name = notification[1].from_name;
                        var ringtone = notification[1].ringtone;
                        var caller_partner_id = notification[1].caller_partner_id;

                        call_sdp = notification[1].sdp;
                        role = "callee";
                        mode = notification[1].mode;

                        var notif_text = from_name + " wants you to join a " + mode;

                        countdown = notification[1].ring_duration;

                        incomingNotification = new VoipCallIncomingNotification(self.notification_manager, "Incoming Call", notif_text, call_id);
	                    self.notification_manager.display(incomingNotification);
	                    mySound = new Audio(ringtone);
	                    mySound.loop = true;
	                    mySound.play();

	                    //Display an image of the person who is calling
	                    $("#voipcallincomingimage").attr('src', '/web/image/res.partner/' + caller_partner_id + '/image_medium/image.jpg');
                        $("#toPartnerImage").attr('src', '/web/image/res.partner/' + caller_partner_id + '/image_medium/image.jpg');

				    } else if (notification[1].direction == 'outgoing') {
					    var to_name = notification[1].to_name;

                        var notif_text = "Calling " + to_name;
                        var callee_partner_id = notification[1].callee_partner_id

                        countdown = notification[1].ring_duration

                        outgoingNotification = new VoipCallOutgoingNotification(self.notification_manager, "Outgoing Call", notif_text, call_id);
	                    self.notification_manager.display(outgoingNotification);

                        //Display an image of the person you are calling
	                    $("#voipcalloutgoingimage").attr('src', '/web/image/res.partner/' + callee_partner_id + '/image_medium/image.jpg');
                        $("#toPartnerImage").attr('src', '/web/image/res.partner/' + callee_partner_id + '/image_medium/image.jpg');
					}

                } else if (notification[0][1] === 'voip.response') {

					var status = notification[1].status;
					var type = notification[1].type;

					console.log("Response: " + status + " | " + type);

					//Destroy the notifcation and stop the countdown because the call was accepted or rejected, no need to wait until timeout
					if (typeof outgoingNotification !== "undefined") {
						clearInterval(outgoing_ring_interval);
					    outgoingNotification.destroy(true);
					}

				} else if(notification[0][1] === 'voip.sdp') {
                    var sdp = notification[1].sdp;
                    console.log("Got SDP Type: " + sdp.type);
                    console.log("Got SDP Data: " + sdp.sdp);

                    window.peerConnection.setRemoteDescription(new RTCSessionDescription(sdp)).then(function() {
						console.log("Set Remote Description");
                        // Only create answers in response to offers
                        if(sdp.type == 'offer') {
							console.log("Create SDP Answer");
                            window.peerConnection.createAnswer().then(createdDescription).catch(errorHandler);
                        }

                        got_remote_description = true;
                        processIceQueue();

                    }).catch(errorHandler);

				} else if(notification[0][1] === 'voip.ice') {
                    var ice = notification[1].ice;

                    console.log("Got Ice Candidate");

				    //Queue the ICE candidates that come before remote description is set
					ice_candidate_queue.push(ice);

                    if (got_remote_description) {
                        processIceQueue();
				    }

				} else if(notification[0][1] === 'voip.end') {
                    console.log("Call End");

                    //Stop all audio / video tracks
                    if (localStream) {
                        localStream.getTracks().forEach(track => track.stop());
				    }

                    if (remoteStream) {
                        remoteStream.getTracks().forEach(track => track.stop());
				    }

					//Destroy the notifcation and stop the countdown because the call was accepted or rejected, no need to wait until timeout
					if (typeof outgoingNotification !== "undefined") {
						clearInterval(outgoing_ring_interval);
					    outgoingNotification.destroy(true);
					}

					if (typeof incomingNotification !== "undefined") {
				        clearInterval(call_interval);
				        incomingNotification.destroy(true);

                        mySound.pause();
                        mySound.currentTime = 0;
					}

                    $("#voip_text").html("Starting Call...");
                    $(".s-voip-manager").css("display","none");



				    got_remote_description = false;

				}


            }).bind(this));

        });
        return this._super.apply(this, arguments);
    },

});

function resetCall() {

    //Stop all audio / video tracks
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
	}

    if (remoteStream) {
        remoteStream.getTracks().forEach(track => track.stop());
	}

	//Destroy the notifcation and stop the countdown because the call was accepted or rejected, no need to wait until timeout
	if (typeof outgoingNotification !== "undefined") {
	    clearInterval(outgoing_ring_interval);
		outgoingNotification.destroy(true);
	}

	if (typeof incomingNotification !== "undefined") {
		clearInterval(call_interval);
		incomingNotification.destroy(true);

        mySound.pause();
        mySound.currentTime = 0;
    }

    $("#voip_text").html("Starting Call...");
    $(".s-voip-manager").css("display","none");

	got_remote_description = false;

}

function errorHandler(error) {
    console.log(error);
}

function onMessage(message) {


    if (message.body.includes("<isComposing") ) {
	    console.log("Composing Message");
    } else {
        //Show the messenger
        $(".s-chat-manager").css("display","block");

        //Add the message to the chat log
        $("#sip-message-log").append("<-" + message.body + "<br/>");

        var aor = message.remoteIdentity.uri.user + "@" + message.remoteIdentity.uri.host

        $("#sip-panel-uri").html(message.remoteIdentity.displayName)

        window.to_sip = aor;

    }

}

function onInvite(session) {

    console.log("Call Type: SIP");

    $(".s-voip-manager").css("display","block");

    window.sip_session = session;



    mode = "audiocall";
    call_type = "external";

    var aor = session.remoteIdentity.uri.user + "@" + session.remoteIdentity.uri.host;

    rpc.query({
        model: 'voip.server',
	    method: 'sip_call_notify',
	    args: [mode, call_type, aor]
    }).then(function(result){
        console.log("Incoming SIP Call Notify");
    });

}

function onPresence(notification) {
    console.log("Presence");
    console.log(notification.request.body);
}


function processIceQueue() {
    console.log("Process Ice Queue");
    for (var i = ice_candidate_queue.length - 1; i >= 0; i--) {
        console.log("Add ICE Candidate:");
        console.log(ice_candidate_queue[i]);

		window.peerConnection.addIceCandidate(new RTCIceCandidate( ice_candidate_queue[i] )).catch(errorHandler);
		ice_candidate_queue.splice(i, 1);
    }

}

function createCall(description) {

    window.peerConnection.setLocalDescription(description).then(function() {

        //Send the call notification to the callee
        rpc.query({
		    model: 'voip.server',
		    method: 'voip_call_notify',
		    args: [mode, to_partner_id, call_type, description]
		}).then(function(result){
            console.log("Notify Callee of incoming phone call");
        });

    }).catch(errorHandler);
}

function createdDescription(description) {

    window.peerConnection.setLocalDescription(description).then(function() {

        rpc.query({
		    model: 'voip.call',
		    method: 'voip_call_sdp',
		    args: [[call_id], description]
		}).then(function(result){
            console.log("Send SDP: " + description);
        });

    }).catch(errorHandler);
}

function messageBankDescription(description) {
    console.log('Created Message Bank Description: ' + description.sdp);

    window.peerConnection.setLocalDescription(description).then(function() {

        //Send the sdp offer to the server
        rpc.query({
		    model: 'voip.call',
		    method: 'message_bank',
		    args: [[call_id], description]
		}).then(function(result){
            console.log("Message Bank Call");
        });


    }).catch(errorHandler);
}

function gotIceCandidate(event) {
    if(event.candidate != null) {

        rpc.query({
		    model: 'voip.call',
		    method: 'voip_call_ice',
		    args: [[call_id], event.candidate]
		}).then(function(result){
		    console.log("Send ICE Candidate: " + event.candidate);
        });

    }
}

function gotRemoteStream(event) {
    console.log("Got Remote Stream: " + event.stream);
    remoteVideo.srcObject = event.stream;
    remoteStream = event.stream;

    var startDate = new Date();

    //Hide the image and replace it with the video stream
    $("#toPartnerImage").css('display','none');
    $("#remoteVideo").css('display','block');

    //For calls with multiple streams (e.g. video calls) this get called twice so we use time difference as a work around
    call_interval = setInterval(function() {
		var endDate = new Date();
		var seconds = (endDate.getTime() - startDate.getTime()) / 1000;

        $("#voip_text").html( Math.round(seconds) + " seconds");
    }, 1000);


    rpc.query({
	    model: 'voip.call',
	    method: 'begin_call',
	    args: [[call_id]],
	    context: weContext.get()
    }).then(function(result){
        console.log("Begin Call");
    });

}

function sipOnError(request) {
    var cause = request.cause;

    if (cause === SIP.C.causes.REJECTED) {
        alert("Call was rejected");
    } else {
		console.log("SIP Call Error");
	    console.log(cause);
	    alert(request.cause);
	}
}

var chatSubscription;

$(document).on('click', '#voip_end_call', function(){

    if (call_type == "external") {
        window.sip_session.bye();
    } else {

        rpc.query({
		    model: 'voip.call',
		    method: 'end_call',
		    args: [[call_id]]
		}).then(function(result){
            console.log("End Call");
        });
    }

});

$(document).on('click', '#sip_message_send_button', function(){
    window.userAgent.message(window.to_sip, $("#sip_address_textbox").val() );

    //Add the message to the chat log
    $("#sip-message-log").append("->" + $("#sip_address_textbox").val() + "<br/>");

    //Clear the message
    $("#sip_address_textbox").val("");

    //TODO also add to chatter
});

$(document).on('click', '#voip_create_window', function(){
    console.log("Create Window");
    var myWindow = window.open("/voip/window", "Voip Call in Progress", "width=500,height=500");

    //Transfer the stream to the popup window
    myWindow.getElementById('remoteVideo').src = remoteVideo.src;

    //TODO??? Close the model to free up space or maybe keep it there as a fallback if popup is closed
});

$(document).on('click', '#voip_full_screen', function(){
    $(".s-voip-manager").css("width","calc(100vw - 20px)");
    $(".s-voip-manager").css("height","calc(100vh - 20px)");
    $(".s-voip-manager").css("left","0px");
    $(".s-voip-manager").css("top","0px");
    $(".s-voip-manager").css("margin","10px");
    $(".s-voip-manager").css("resize","none");
    $("#remoteVideo").css("width","auto");
});

var VoipCallOutgoingNotification = Notification.extend({
    template: "VoipCallOutgoingNotification",

    init: function(parent, title, text, call_id) {
        this._super(parent, title, text, true);
    },
    start: function() {
        myNotif = this;
        this._super.apply(this, arguments);
        secondsLeft = countdown;
        $("#callsecondsoutgoingleft").html(secondsLeft);

        outgoing_ring_interval = setInterval(function() {
            $("#callsecondsoutgoingleft").html(secondsLeft);
            if (secondsLeft == 0) {

                rpc.query({
		            model: 'voip.call',
		            method: 'miss_call',
		            args: [[call_id]]
		        }).then(function(result){
				    console.log("Missed Call");
				});

                //Send the offer to message bank (server)
                /*
                if (mode == "audiocall") {
		            window.peerConnection.createOffer().then(messageBankDescription).catch(errorHandler);
			    }
			    */

				//Play the missed call audio
				mySound = new Audio("/voip/miss/" + call_id + ".mp3");
				mySound.play();

				clearInterval(outgoing_ring_interval);
				resetCall();
                myNotif.destroy(true);
            }

            secondsLeft--;
        }, 1000);

    },
});

var VoipCallIncomingNotification = Notification.extend({
    template: "VoipCallIncomingNotification",

    init: function(parent, title, text, call_id) {
        this._super(parent, title, text, true);


        this.events = _.extend(this.events || {}, {
            'click .link2accept': function() {

                rpc.query({
		            model: 'voip.call',
		            method: 'accept_call',
		            args: [[call_id]],
		            context: weContext.get()
		        }).then(function(result){
                    console.log("Accept Call");
                });

                //Clear the countdown now
                clearInterval(incoming_ring_interval);

                mySound.pause();
                mySound.currentTime = 0;

                //Constraints are slightly different for the callee e.g. for callee we don't need screen sharing access only audio
                var constraints = {};
                if (mode == "videocall") {
                    constraints = {audio: true, video: true};
                } else if (mode == "audiocall") {
                    constraints = {audio: true};
                } else if (mode == "screensharing") {
					//constraints = {'audio': true, 'OfferToReceiveVideo': true};
					constraints = {'audio': true, 'video': {'mediaSource': "screen"}};
                }

                console.log(call_type);
                console.log(constraints);
                if (call_type == "external") {
					console.log("Accept SIP Call");

					console.log(window.sip_session);

                    window.sip_session.accept({
                        media: {
							constraints: {
							    audio: true
                            },
                            render: {
                                remote: document.getElementById('remoteVideo'),
                                local: document.getElementById('localVideo')
                            }
                        }
                    });

                    window.sip_session.on('failed', sipOnError);
                    window.sip_session.on('bye', resetCall);

                } else {

                    //Ask for media access only if the call is accepted
                    if (navigator.webkitGetUserMedia) {
				        navigator.webkitGetUserMedia(constraints, getUserMediaSuccess, getUserMediaError);
			        } else {
                        window.navigator.mediaDevices.getUserMedia(constraints).then(getUserMediaSuccess).catch(getUserMediaError);
			        }
                }

                this.destroy(true);
            },

            'click .link2reject': function() {

                rpc.query({
		            model: 'voip.call',
		            method: 'reject_call',
		            args: [[call_id]]
		        }).then(function(result){
                    console.log("Reject Call");
                });

                //Clear the countdown now
                clearInterval(incoming_ring_interval);

                mySound.pause();
                mySound.currentTime = 0;
                this.destroy(true);
            },
        });
    },
    start: function() {
        myNotif = this;
        this._super.apply(this, arguments);
        secondsLeft = countdown;
        $("#callsecondsincomingleft").html(secondsLeft);

        incoming_ring_interval = setInterval(function() {
            $("#callsecondsincomingleft").html(secondsLeft);
            if (secondsLeft == 0) {
                mySound.pause();
                mySound.currentTime = 0;
                resetCall();
                clearInterval(incoming_ring_interval);
                myNotif.destroy(true);
            }

            secondsLeft--;
        }, 1000);

    },
});


return {
    VoipCallClient: VoipCallClient,
};


});