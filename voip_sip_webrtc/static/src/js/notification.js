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

var _t = core._t;
var qweb = core.qweb;

var mySound = "";
var secondsLeft = "30";
var call_id = "";
var myNotif = "";

WebClient.include({

    show_application: function() {

        bus.on('notification', this, function (notifications) {
            _.each(notifications, (function (notification) {
                if (notification[0][1] === 'voip.notification') {
					var self = this;
					var ringtone = notification[1].ringtone;
					call_id = notification[1].call_id;
					var from_name = notification[1].from_name;

                    var notif_text = from_name + " is calling";

                    var notification = new VoipCallNotification(self.notification_manager, "Incoming Call", notif_text, call_id);
	                self.notification_manager.display(notification);
	                mySound = new Audio(ringtone);
	                mySound.loop = true;
	                mySound.play();
                } else if(notification[0][1] === 'voip.call') {
					alert("Call data");
				}
            }).bind(this));

        });
        return this._super.apply(this, arguments);
    },

});

var VoipCallNotification = Notification.extend({
    template: "VoipCallNotification",

    init: function(parent, title, text, call_id) {
        this._super(parent, title, text, true);


        this.events = _.extend(this.events || {}, {
            'click .link2accept': function() {
                window.location.href = "/voip/accept/" + call_id;
                mySound.pause();
                mySound.currentTime = 0;
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
        $("#callsecondsleft").html(secondsLeft);

        var interval = setInterval(function() {
            $("#callsecondsleft").html(secondsLeft);
            if (secondsLeft == 0) {
				myNotif.rpc("/voip/missed/" + call_id);
                mySound.pause();
                mySound.currentTime = 0;
                clearInterval(interval);
                myNotif.destroy(true);
            }

            secondsLeft--;
        }, 1000);

    },
});


});