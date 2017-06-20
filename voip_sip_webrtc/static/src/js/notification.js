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

var _t = core._t;
var qweb = core.qweb;

ajax.loadXML('/voip_sip_webrtc/static/src/xml/voip_window2.xml', qweb);

var mySound = "";
var countdown;
var secondsLeft;
var callSeconds;
var call_id = "";
var myNotif = "";
var outgoingNotification
var role;
var mode = false;
var call_type = ""
var to_partner_id;
var outgoing_ring_interval;


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

	    session.rpc('/voip/user/list', {}).then(function(result) {

            $("#voip_tray").html("");

	        for (var voip_user in result) {
				var voip_user = result[voip_user];
				var drop_menu_html = "";

				drop_menu_html += "<li>";
				drop_menu_html += "  " + "<a href=\"#\">" + voip_user.name + "</a>" + " <a href=\"#\" data-partner=\"" + voip_user.partner_id + "\" class=\"start_voip_video_call\"><i class=\"fa fa-video-camera\" aria-hidden=\"true\"/> Video Call</a> <a href=\"#\" data-partner=\"" + voip_user.partner_id + "\" class=\"start_voip_audio_call\"><i class=\"fa fa-volume-up\" aria-hidden=\"true\"/> Audio Call</a> <a href=\"#\" data-partner=\"" + voip_user.partner_id + "\" class=\"start_voip_screenshare_call\"><i class=\"fa fa-desktop\" aria-hidden=\"true\"/> Screenshare Call</a>";
				drop_menu_html += "</li>";


				/*
				drop_menu_html += "<li class=\"dropdown-submenu\">";
				drop_menu_html += "  <a tabindex=\"-1\" href=\"#\">" + voip_user.name + " <span class=\"caret\"/></a>";
				drop_menu_html += "  <ul class=\"dropdown-menu\">";
				drop_menu_html += "    <li><a href=\"#\">Video Call</a></li>";
				drop_menu_html += "    <li><a href=\"#\">Audio Call</a></li>";
				drop_menu_html += "  </ul>";
				drop_menu_html += "</li>";
				*/

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

                        role = "callee";
                        mode = notification[1].mode;

                        var notif_text = from_name + " wants you to join a " + mode;

                        countdown = notification[1].ring_duration;

                        var incomingNotification = new VoipCallIncomingNotification(self.notification_manager, "Incoming Call", notif_text, call_id);
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

					//Destroy the notifcation because the call was accepted or rejected, no need to wait until timeout
					if (typeof outgoingNotification !== "undefined") {
					    outgoingNotification.destroy(true);
					}

				} else if(notification[0][1] === 'voip.sdp') {
                    var sdp_json = notification[1].sdp;
                    var sdp = JSON.parse(sdp_json)['sdp'];
                    console.log("Got SDP " + sdp.type);
                    console.log(sdp);

                    window.peerConnection.setRemoteDescription(new RTCSessionDescription(sdp)).then(function() {
						console.log("Set Remote Description");
                        // Only create answers in response to offers
                        if(sdp.type == 'offer') {
							console.log("Create SDP Answer");
                            window.peerConnection.createAnswer().then(createdDescription).catch(errorHandler);
                        }
                    }).catch(errorHandler);

				} else if(notification[0][1] === 'voip.ice') {
                    var ice_json = notification[1].ice;
                    var ice = JSON.parse(ice_json)['ice'];
                    console.log("Got Remote ICE Candidate");
                    console.log(ice_json);
					peerConnection.addIceCandidate(new RTCIceCandidate(ice)).catch(errorHandler);
				} else if(notification[0][1] === 'voip.end') {
                    console.log("Call End");

                    //Stop all audio / video tracks
                    localStream.getTracks().forEach(track => track.stop());
                    remoteStream.getTracks().forEach(track => track.stop());

                    $(".s-voip-manager").css("opacity","0");
				}


            }).bind(this));

        });
        return this._super.apply(this, arguments);
    },

});

function errorHandler(error) {
    console.log(error);
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
    window.peerConnection.ontrack = gotRemoteStream;
    window.peerConnection.addStream(localStream);

    if (role == "caller") {
		//Show the VOIP Manager now because we may need it if we go to message bank
        console.log("Notify Callee of incoming phone call");

        $.ajax({
	        method: "GET",
	    	url: "/voip/call/notify",
		    data: { mode: mode, to_partner_id: to_partner_id, call_type: call_type },
            success: function(data) {

            }
        });
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

function createdDescription(description) {
    console.log('createdDescription: ' + description);

    window.peerConnection.setLocalDescription(description).then(function() {

        $.ajax({
	        method: "GET",
	    	url: "/voip/call/sdp",
	    	data: { call: call_id, sdp: JSON.stringify({'sdp': peerConnection.localDescription}) },
            success: function(data) {

            }
        });

    }).catch(errorHandler);
}

function messageBankDescription(description) {
    console.log('created Message Bank Description: ' + description);

    window.peerConnection.setLocalDescription(description).then(function() {

    //Send the sdp offer to the server
    session.rpc('/voip/messagebank', {'voip_call_id': call_id, 'sdp': "test"}).then(function(result) {

    });


    }).catch(errorHandler);
}

function gotIceCandidate(event) {
    if(event.candidate != null) {
		console.log("Send ICE Candidate: " + event.candidate);

        $.ajax({
	        method: "GET",
	    	url: "/voip/call/ice",
	    	data: { call: call_id, ice: JSON.stringify({'ice': event.candidate}) },
            success: function(data) {

            }
        });
    }
}

function gotRemoteStream(event) {
    console.log("Got Remote Stream: " + event.streams[0].id);
    remoteVideo.srcObject = event.streams[0];
    remoteStream = event.streams[0];
    clearInterval(outgoing_ring_interval);

    var startDate = new Date();

    //Hide the image and replace it with the video stream
    $("#toPartnerImage").css('display','none');
    $("#remoteVideo").css('display','block');

    //For video calls (2 streams) this get called twice so we use time difference as a work around
    var call_interval = setInterval(function() {
		var endDate   = new Date();
		var seconds = (endDate.getTime() - startDate.getTime()) / 1000;

        $("#voip_text").html( Math.round(seconds) + " seconds");
    }, 1000);

    $.ajax({
	    method: "GET",
		url: "/voip/call/begin",
		data: { call: call_id },
        success: function(data) {

        }
    });
}

$(document).on('click', '#voip_end_call', function(){

    $.ajax({
	    method: "GET",
		url: "/voip/call/end",
		data: { call: call_id },
        success: function(data) {

        }
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
				console.log("Missed Call");

				myNotif.rpc("/voip/missed/" + call_id);

                //Send the offer to message bank (server)
		        //window.peerConnection.createOffer().then(messageBankDescription).catch(errorHandler);

				//Play the missed call audio
				mySound = new Audio("/voip/miss/" + call_id + ".mp3");
				mySound.play();

				clearInterval(outgoing_ring_interval);
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

                this.rpc("/voip/accept/" + call_id);
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

				this.rpc("/voip/reject/" + call_id);
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

        var incoming_ring_interval = setInterval(function() {
            $("#callsecondsincomingleft").html(secondsLeft);
            if (secondsLeft == 0) {
				//myNotif.rpc("/voip/missed/" + call_id);
                mySound.pause();
                mySound.currentTime = 0;
                clearInterval(incoming_ring_interval);
                myNotif.destroy(true);
            }

            secondsLeft--;
        }, 1000);

    },
});


});