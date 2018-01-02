odoo.define('voip_sip_webrtc_website.front', function (require) {
'use strict';

var bus = require('bus.bus').bus;
var session = require('web.session');

    $(function() {

        bus.on('notification', this, function (notifications) {
            var self = this;
            _.each(notifications, function (notification) {
                alert("Notification");
            });
        });

        //Global Variables
        var call_id = "";

	    //Add the voip window
		var voip_window_html = "";
		voip_window_html += "<div class=\"s-front-voip-manager\">\n"
		voip_window_html += "  <div class=\"voip-front-controls-panel\">\n"
		voip_window_html += "    <button id=\"voip_end_call\" class=\"btn btn-danger\" style=\"width:90px;margin:5px;\" type=\"button\">End Call</button>\n"
		voip_window_html += "    <p id=\"voip_text\" style=\"text-align:center;\">Starting Call...</p>\n"
		voip_window_html += "  </div>\n"
		voip_window_html += "  <div class=\"voip-front-video-container\">\n"
		voip_window_html += "    <video id=\"remoteVideo\" autoplay=\"autoplay\" style=\"height:100%;width:100%;display:none;\"/>\n"
		voip_window_html += "    <video id=\"localVideo\" autoplay=\"autoplay\" muted=\"muted\" style=\"display:none;\"/>\n"
		voip_window_html += "  </div>\n"
		voip_window_html += "</div>\n"
		$("body").append(voip_window_html);

        //Request Media access on click
		$( ".voip-c2c" ).click(function() {

            var contraints = {'audio': true, 'video': true};

            if (navigator.webkitGetUserMedia) {
		        navigator.webkitGetUserMedia(contraints, getUserMediaSuccess, getUserMediaError);
		    } else {
                window.navigator.mediaDevices.getUserMedia(contraints).then(getUserMediaSuccess).catch(getUserMediaError);
		    }

	    });

        function getUserMediaSuccess(stream) {

            console.log("Got Media Access");

            $(".s-front-voip-manager").css("opacity","1");

            //Set the local stream
	        $('#localVideo').src = window.URL.createObjectURL(stream);

            var peerConnectionConfig = {
                'iceServers': [
                    {'urls': 'stun:stun.services.mozilla.com'},
                    {'urls': 'stun:stun.l.google.com:19302'},
                ]
            };

            window.peerConnection = new RTCPeerConnection(peerConnectionConfig);
            window.peerConnection.onicecandidate = gotIceCandidate;
            window.peerConnection.onaddstream = gotRemoteStream;
            window.peerConnection.addStream(stream);

		    window.peerConnection.createOffer().then( function (description) {

                window.peerConnection.setLocalDescription(description).then(function() {


                    //TODO pass the clicked button here to deal with pages with multiple buttons
                    var button_id = $(".voip-button").data("voip-button-id");
                    console.log(button_id);
                    console.log(description.sdp);

			        session.rpc('/voip/button/call/' + button_id, {'sdp': description.sdp}).then(function(result) {
						//TODO display ring countdown and return error if callee is busy
                        call_id = result.voip_call_id;

                        bus.add_channel('voip.website.sdp' + call_id);
                        bus.start_polling();

                        console.log("Notify Callee of incoming phone call" + call_id);

                    });


                }).catch(errorHandler);

		    }).catch(errorHandler);


        }

        function gotIceCandidate(event) {
            if(event.candidate != null) {

			    session.rpc('/voip/button/ice/' + call_id, {'ice': event.candidate}).then(function(result) {
		            console.log("Send ICE Candidate: " + event.candidate);
                });

            }
        }

        function gotRemoteStream(event) {
            console.log("Got Remote Stream: " + event.stream);
            remoteVideo.srcObject = event.stream;
            remoteStream = event.stream;

            var startDate = new Date();

            //Display the Video
            $("#remoteVideo").css('display','block');

            //For calls with multiple streams (e.g. video calls) this get called twice so we use time difference as a work around
            call_interval = setInterval(function() {
        		var endDate = new Date();
        		var seconds = (endDate.getTime() - startDate.getTime()) / 1000;

                $("#voip_text").html( Math.round(seconds) + " seconds");
            }, 1000);



        }

	    function getUserMediaError(error) {
		    console.log("Failed to access to media: " + error);
		    alert("Failed to access to media: " + error.name);
        };

        function errorHandler(error) {
		    console.log(error);
		    alert(error);
        }
    });

});