odoo.define('voip_sip_webrtc.voip_call_notification', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var Model = require('web.DataModel');
var odoo_session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var bus = require('bus.bus').bus;
var Notification = require('web.notification').Notification;
var WebClient = require('web.WebClient');
var SystrayMenu = require('web.SystrayMenu');
var form_common = require('web.form_common');
var form_widgets = require('web.form_widgets');

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
            var model = new Model("voip.server");
            model.call("voip_call_notify", [[call_id]], {'mode': mode, 'to_partner_id': to_partner_id, 'call_type': call_type, 'sdp': ''}).then(function(result) {
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


        var model = new Model("voip.server");
        model.call("get_user_agent", [[]]).then(function(result) {


            if (result.address != '') {
				console.log("Signing in as " + result.address);
                window.userAgent = new SIP.UA({
                    uri: result.address,
                    wsServers: [result.wss],
                    authorizationUser: result.auth_username,
                    password: result.password
                });

                window.userAgent.start();
                window.userAgent.on('message', onMessage);
                window.userAgent.on('invite', onInvite);
		    }


        });



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

    var model = new Model("voip.server");
    model.call("sip_call_notify", [[]], {'mode': mode, 'call_type': call_type, 'aor': aor}).then(function(result) {
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
        var model = new Model("voip.server");
        console.log(description);
        model.call("voip_call_notify", [[call_id]], {'mode': mode, 'to_partner_id': to_partner_id, 'call_type': call_type, 'sdp': description}).then(function(result) {
            console.log("Notify Callee of incoming phone call");
        });

    }).catch(errorHandler);
}

function createdDescription(description) {

    window.peerConnection.setLocalDescription(description).then(function() {

        var model = new Model("voip.call");
        model.call("voip_call_sdp", [[call_id]], {'sdp': description}).then(function(result) {
            console.log("Send SDP: " + description);
        });

    }).catch(errorHandler);
}

function messageBankDescription(description) {
    console.log('Created Message Bank Description: ' + description.sdp);

    window.peerConnection.setLocalDescription(description).then(function() {

        //Send the sdp offer to the server
        var model = new Model("voip.call");
        model.call("message_bank", [[call_id]], {'sdp': description}).then(function(result) {
            console.log("Message Bank Call");
        });


    }).catch(errorHandler);
}

function gotIceCandidate(event) {
    if(event.candidate != null) {

        var model = new Model("voip.call");
        model.call("voip_call_ice", [[call_id]], {'ice': event.candidate}).then(function(result) {
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


    var model = new Model("voip.call");
    model.call("begin_call", [[call_id]], {}).then(function(result) {
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

var FieldSIP = form_widgets.FieldChar.extend({
    events: {
        'click .sip-call': 'start_sip_call',
        'click .sip-video': 'start_sip_video',
        'click .sip-message': 'open_sip_messenger',
    },
    init: function() {
        this._super.apply(this, arguments);
        this.clickable = true;
    },
    render_value: function() {
        this._super();


        if (this.get("effective_readonly")) {


            if (this.get("value") && window.userAgent) {
                console.log("Listening for " + this.get("value") + " presence information");
                window.chatSubscription = window.userAgent.subscribe(this.get("value"), 'presence');

                //We update the widget once we get presence information so a person doesn't try to call someone who isn't available
                window.chatSubscription.on('notify', onPresence);
		    }

		    this.$el.html("<span style=\"float:right\"><i class=\"fa fa-comments sip-message\" aria-hidden=\"true\"></i> <i class=\"fa fa-phone sip-call\" aria-hidden=\"true\"></i> <i class=\"fa fa-video-camera sip-video\" aria-hidden=\"true\"></i></span><span style=\"display: block;width: 170px;overflow: hidden;white-space: nowrap;text-overflow: ellipsis;\">" + this.get("value") + "</span>");

        } else {
			if (this.get("value")) {
			    this.$input.val(this.get("value"));
		    }
        }

    },
    start_sip_call: function() {

        console.log("Call Type: SIP");

        $(".s-voip-manager").css("display","block");

        //Here you determine if the call has audio and video
        var options = {
            media: {
                constraints: {
                    audio: true
                 },
                render: {
                    remote: document.getElementById('remoteVideo'),
                    local: document.getElementById('localVideo')
                }
            }
        };

        //Make the audio call
        console.log("SIP audio calling: " + this.get("value"));
        window.sip_session = window.userAgent.invite(this.get("value"), options);

        window.sip_session.on('failed', sipOnError);

    },
    start_sip_video: function() {

        console.log("Call Type: SIP Video");

        $(".s-voip-manager").css("display","block");

        //Here you determine if the call has audio and video
        var options = {
            media: {
                constraints: {
                    audio: true,
                    video: true
                 },
                render: {
                    remote: document.getElementById('remoteVideo'),
                    local: document.getElementById('localVideo')
                }
            }
        };

        //Make the video call
        window.sip_session = window.userAgent.invite('sip:' + this.get("value"), options);

        window.sip_session.on('failed', sipOnError);

    },
    open_sip_messenger: function() {

        console.log("Message Type: SIP");
        console.log(this.get("value"));

        window.to_sip = this.get("value");
        $(".s-chat-manager").css("display","block");

    }

});

var FieldSIPPSTN = form_widgets.FieldChar.extend({
    events: {
        'click .sip-pstn-call': 'start_pstn_call',
    },
    init: function() {
        this._super.apply(this, arguments);
        this.clickable = true;
    },
    render_value: function() {
        this._super();


        if (this.get("effective_readonly")) {
		    this.$el.html("<span>" + this.get("value") + "</span> <i class=\"fa fa-phone sip-pstn-call\" aria-hidden=\"true\"></i>");
        } else {
			this.$input.val(this.get("value"));
        }

    },
    start_pstn_call: function() {

        console.log("Call Type: PSTN");

        $(".s-voip-manager").css("display","block");

        //Make the audio call
        console.log("PSTN audio calling: " + this.get("value"));

        role = "caller";
        mode = "audiocall";
        call_type = "external";
        to_partner_id = 7;

        var contraints = {'audio': true};

        if (navigator.webkitGetUserMedia) {
		    navigator.webkitGetUserMedia(contraints, getUserMediaSuccess, getUserMediaError);
		} else {
            window.navigator.mediaDevices.getUserMedia(contraints).then(getUserMediaSuccess).catch(getUserMediaError);
		}

    }
});

core.form_widget_registry.add('sip', FieldSIP)
core.form_widget_registry.add('sippstn', FieldSIPPSTN)


$(document).on('click', '#voip_end_call', function(){

    if (call_type == "external") {
        window.sip_session.bye();
    } else {
        var model = new Model("voip.call");
        model.call("end_call", [[call_id]], {}).then(function(result) {
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

                var model = new Model("voip.call");
                model.call("miss_call", [[call_id]], {}).then(function(result) {
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

                var model = new Model("voip.call");
                model.call("accept_call", [[call_id]], {}).then(function(result) {
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

                var model = new Model("voip.call");
                model.call("reject_call", [[call_id]], {}).then(function(result) {
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