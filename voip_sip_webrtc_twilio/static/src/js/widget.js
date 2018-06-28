odoo.define('voip_sip_webrtc_twilio.voip_twilio_call_notification', function (require) {
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

var call_conn;
var myNotif = "";
var secondsLeft;
var incoming_ring_interval;
var mySound = "";

$(function() {

    rpc.query({
        model: 'voip.number',
		method: 'get_numbers',
		args: [],
		context: weContext.get()
    }).then(function(result){

        for (var i = 0; i < result.length; i++) {
            var call_route = result[i];

            console.log("Signing in as " + call_route.capability_token_url);

            $.getJSON(call_route.capability_token_url).done(function (data) {
                console.log('Got a token.');
                console.log('Token: ' + data.token);
                console.log("Set Client Name: " + data.identity);

                rpc.query({
                    model: 'res.users',
		            method: 'update_twilio_client_name',
		            args: [[odoo_session.uid], data.identity],
		            context: weContext.get()
               }).then(function(result){
                   console.log("Identity Set");
               });

                // Setup Twilio.Device
                Twilio.Device.setup(data.token);

                Twilio.Device.ready(function (device) {
                    console.log('Twilio.Device Ready!');
                });

            })
            .fail(function () {
                console.log('Could not get a token from server!');
            });

		}

    });
});


// Bind to end call button
$(document).on("click", "#voip_end_call", function(){
    console.log('Hanging up...');
    twilio_end_call();
});

function twilio_end_call() {
	console.log('Call ended.');
    $("#voip_text").html("Starting Call...");
    $(".s-voip-manager").css("display","none");
    Twilio.Device.disconnectAll();
}

Twilio.Device.connect(function (conn) {
    console.log('Successfully established call!');

    $(".s-voip-manager").css("display","block");

    var startDate = new Date();
    var call_interval;

    call_interval = setInterval(function() {
        var endDate = new Date();
        var seconds = (endDate.getTime() - startDate.getTime()) / 1000;
        $("#voip_text").html( Math.round(seconds) + " seconds");
    }, 1000);
});

Twilio.Device.disconnect(function (conn) {
    twilio_end_call();
});

Twilio.Device.incoming(function (conn) {
    console.log('Incoming connection from ' + conn.parameters.From);

    //Set it on a global scale because we we need it when the call it accepted or rejected inside the incoming call dialog
    call_conn = conn;

    //Poll the server so we can find who the call is from + ringtone
    rpc.query({
        model: 'res.users',
	    method: 'get_call_details',
	    args: [[odoo_session.uid], conn],
	    context: weContext.get()
    }).then(function(result){

        //Open the incoming call dialog
	    var self = this;

	    var from_name = result.from_name;
        var ringtone = result.ringtone;
        var caller_partner_id = result.caller_partner_id;
        window.countdown = result.ring_duration;

        var notif_text = from_name + " wants you to join a mobile call";

        var incomingNotification = new VoipTwilioCallIncomingNotification(window.swnotification_manager, "Incoming Call", notif_text, 0);
	    window.swnotification_manager.display(incomingNotification);
	    mySound = new Audio(ringtone);
	    mySound.loop = true;
	    mySound.play();

	    //Display an image of the person who is calling
	    $("#voipcallincomingimage").attr('src', '/web/image/res.partner/' + caller_partner_id + '/image_medium/image.jpg');
        $("#toPartnerImage").attr('src', '/web/image/res.partner/' + caller_partner_id + '/image_medium/image.jpg');

    });

});

Twilio.Device.error(function (error) {
    console.log('Twilio.Device Error: ' + error.message);
    alert(error.message);
});

var VoipTwilioCallIncomingNotification = Notification.extend({
    template: "VoipCallIncomingNotification",

    init: function(parent, title, text, call_id) {
        this._super(parent, title, text, true);


        this.events = _.extend(this.events || {}, {
            'click .link2accept': function() {

                call_conn.accept();

                this.destroy(true);
            },

            'click .link2reject': function() {

                call_conn.reject();

                this.destroy(true);
            },
        });
    },
    start: function() {
        myNotif = this;
        this._super.apply(this, arguments);
        secondsLeft = window.countdown;
        $("#callsecondsincomingleft").html(secondsLeft);

        incoming_ring_interval = setInterval(function() {
            $("#callsecondsincomingleft").html(secondsLeft);
            if (secondsLeft == 0) {
                mySound.pause();
                mySound.currentTime = 0;
                clearInterval(incoming_ring_interval);
                myNotif.destroy(true);
            }

            secondsLeft--;
        }, 1000);

    },
});

WebClient.include({

    show_application: function() {

        window.swnotification_manager = this.notification_manager;

        bus.on('notification', this, function (notifications) {
            _.each(notifications, (function (notification) {

                  if (notification[0][1] === 'voip.twilio.start') {
                      var self = this;

                      var from_number = notification[1].from_number;
                      var to_number = notification[1].to_number;
                      var capability_token_url = notification[1].capability_token_url;

                      console.log("Call Type: Twilio");

                      //Make the audio call
                      console.log("Twilio audio calling: " + to_number);

                      var params = {
                          From: from_number,
                          To: to_number
                      };

                      console.log('Calling ' + params.To + '...');

                      $.getJSON(capability_token_url).done(function (data) {
                          // Setup Twilio.Device
                          Twilio.Device.setup(data.token);
                          Twilio.Device.connect(params);
                      }).fail(function () {
                          console.log('Could not get a token from server!');
                      });

                }


            }).bind(this));

        });
        return this._super.apply(this, arguments);
    },

});

});