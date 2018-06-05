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
var Widget = require('web.Widget');
var fieldRegistry = require('web.field_registry');

var basicFields = require('web.basic_fields');
var FieldChar = basicFields.FieldChar;
var InputField = basicFields.InputField;
var TranslatableFieldMixin = basicFields.TranslatableFieldMixin;

var _t = core._t;
var qweb = core.qweb;

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

Twilio.Device.error(function (error) {
    console.log('Twilio.Device Error: ' + error.message);
    alert(error.message);
});

WebClient.include({

    show_application: function() {

        console.log("Start Twilio notification");

        bus.on('notification', this, function (notifications) {
            _.each(notifications, (function (notification) {

                  console.log( notification[0][1] );

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