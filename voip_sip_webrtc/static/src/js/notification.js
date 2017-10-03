odoo.define('voip_sip_webrtc.voip_call_notification', function (require) {
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
var SystrayMenu = require('web.SystrayMenu');
var form_common = require('web.form_common');
var form_widgets = require('web.form_widgets');

var _t = core._t;
var qweb = core.qweb;

ajax.loadXML('/voip_sip_webrtc/static/src/xml/voip_window2.xml', qweb);

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

var VOIPItem = Widget.extend({
    template:'VoipSystemTray',
    events: {
        "click": "on_click",
        "click .start_voip_audio_call": "start_voip_audio_call",
        "click .start_voip_video_call": "start_voip_video_call",
        "click .start_voip_screenshare_call": "start_voip_screenshare_call",
    },
    on_click: function (event) {
        event.preventDefault();

        var model = new Model("voip.server");
        model.call("user_list", [[]]).then(function(result) {

            $("#voip_tray").html("");

	        for (var voip_user in result) {
				var voip_user = result[voip_user];
				var drop_menu_html = "";

				drop_menu_html += "<li>";
				drop_menu_html += "  " + "<a href=\"#\">" + voip_user.name + "</a>" + " <a href=\"#\" data-partner=\"" + voip_user.partner_id + "\" class=\"start_voip_video_call\"><i class=\"fa fa-video-camera\" aria-hidden=\"true\"/> Video Call</a> <a href=\"#\" data-partner=\"" + voip_user.partner_id + "\" class=\"start_voip_audio_call\"><i class=\"fa fa-volume-up\" aria-hidden=\"true\"/> Audio Call</a> <a href=\"#\" data-partner=\"" + voip_user.partner_id + "\" class=\"start_voip_screenshare_call\"><i class=\"fa fa-desktop\" aria-hidden=\"true\"/> Screenshare Call</a>";
				drop_menu_html += "</li>";

			    $("#voip_tray").append(drop_menu_html);

			}

        });

    },
    start_voip_screenshare_call: function (event) {
		console.log("Call Type: screenshare call");

        role = "caller";
        mode = "screensharing";
        call_type = "internal";
        to_partner_id = $(event.currentTarget).data("partner");

        var constraints = {'video': {'mediaSource': "screen"}};

        if (navigator.webkitGetUserMedia) {
		    navigator.webkitGetUserMedia(constraints, getUserMediaSuccess, getUserMediaError);
		} else {
            window.navigator.mediaDevices.getUserMedia(constraints).then(getUserMediaSuccess).catch(getUserMediaError);
		}

	},
    start_voip_audio_call: function (event) {
		console.log("Call Type: audio call");

        role = "caller";
        mode = "audiocall";
        call_type = "internal";
        to_partner_id = $(event.currentTarget).data("partner");
		var constraints = {'audio': true};

        if (navigator.webkitGetUserMedia) {
		    navigator.webkitGetUserMedia(constraints, getUserMediaSuccess, getUserMediaError);
		} else {
            window.navigator.mediaDevices.getUserMedia(constraints).then(getUserMediaSuccess).catch(getUserMediaError);
		}

	},
    start_voip_video_call: function (event) {
		console.log("Call Type: video call");

        role = "caller";
        mode = "videocall";
        call_type = "internal";
        to_partner_id = $(event.currentTarget).data("partner");
		var constraints = {'audio': true, 'video': true};

        if (navigator.webkitGetUserMedia) {
		    navigator.webkitGetUserMedia(constraints, getUserMediaSuccess, getUserMediaError);
		} else {
            window.navigator.mediaDevices.getUserMedia(constraints).then(getUserMediaSuccess).catch(getUserMediaError);
		}

	},
});

SystrayMenu.Items.push(VOIPItem);


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

WebClient.include({

    show_application: function() {

        $('body').append(qweb.render('voip_sip_webrtc.VoipWindow', {}));

        $(".s-voip-manager").draggable().resizable({handles: 'ne, se, sw, nw'});

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
                    $(".s-voip-manager").css("opacity","0");



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
    $(".s-voip-manager").css("opacity","0");

	got_remote_description = false;

}

function errorHandler(error) {
    console.log(error);
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

function getUserMediaSuccess(stream) {
    console.log("Got Media Access");

    $(".s-voip-manager").css("opacity","1");

    localVideo = document.querySelector('#localVideo');
    remoteVideo = document.querySelector('#remoteVideo');

    localStream = stream;
	localVideo.src = window.URL.createObjectURL(stream);

    window.peerConnection = new RTCPeerConnection(peerConnectionConfig);
    window.peerConnection.onicecandidate = gotIceCandidate;
    //window.peerConnection.ontrack = gotRemoteStream;
    window.peerConnection.onaddstream = gotRemoteStream;
    window.peerConnection.addStream(localStream);

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

function createCall(description) {

    window.peerConnection.setLocalDescription(description).then(function() {

        //Send the call notification to the callee
        var model = new Model("voip.server");
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


var FieldSIP = form_widgets.FieldChar.extend({
    events: {
        'click .sip-call': 'start_sip_call',
    },
    render_value: function() {
        if (this.get("effective_readonly")) {
		    this.$el.html("" + this.get("value") + " <a href=\"javascript:;\"class=\"fa fa-phone sip-call\" style=\"text-decoration: underline;\" aria-hidden=\"true\"> Call</a>");
        } else {
			this.$input.val(this.get("value"));
        }
    },
    start_sip_call: function() {

        console.log("Call Type: SIP");

        role = "caller";
        mode = "audiocall";
        call_type = "external";
        to_partner_id = this.getParent().get_fields_values()['id'];
    	var constraints = {'audio': true};

        if (navigator.webkitGetUserMedia) {
    	    navigator.webkitGetUserMedia(constraints, getUserMediaSuccess, getUserMediaError);
    	} else {
            window.navigator.mediaDevices.getUserMedia(constraints).then(getUserMediaSuccess).catch(getUserMediaError);
        }


    }
});


core.form_widget_registry.add('sip', FieldSIP)

$(document).on('click', '#voip_end_call', function(){

    var model = new Model("voip.call");
    model.call("end_call", [[call_id]], {}).then(function(result) {
        console.log("End Call");
    });

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

                //Constraints are slightly different for the callee e.g. for calle we don't need screen sharing access only audio
                var constraints = {};
                if (mode == "videocall") {
                    constraints = {audio: true, video: true};
                } else if (mode == "audiocall") {
                    constraints = {audio: true};
                } else if (mode == "screensharing") {
                    constraints = {audio: true};
                }

                //Ask for media access only if the call is accepted
                if (navigator.webkitGetUserMedia) {
					navigator.webkitGetUserMedia(constraints, getUserMediaSuccess, getUserMediaError);
			    } else {
                    window.navigator.mediaDevices.getUserMedia(constraints).then(getUserMediaSuccess).catch(getUserMediaError);
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

});