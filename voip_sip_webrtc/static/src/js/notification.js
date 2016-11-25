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

//var new_channel = JSON.stringify([session.db, 'voip.room', session.uid]);
//bus.add_channel(new_channel);



WebClient.include({

    show_application: function() {

        bus.on('notification', this, function (notifications) {
            _.each(notifications, (function (notification) {
                if (notification[0][1] === 'voip.room') {
					var self = this;
                    var notification = new VoipCallNotification(self.notification_manager, "Incoming Call", "Incoming Call", notification[1].room);
	                self.notification_manager.display(notification);
                }
            }).bind(this));

        });
        return this._super.apply(this, arguments);
    },

});


//bus.trigger('voip_call');

var VoipCallNotification = Notification.extend({
    template: "VoipCallNotification",

    init: function(parent, title, text, room) {
        this._super(parent, title, text, true);

        this.events = _.extend(this.events || {}, {
            'click .link2accept': function() {
                window.location.href = "/voip/accept/" + room;
                this.destroy(true);
            },

            'click .link2reject': function() {
				this.rpc("/voip/reject/" + room);
                this.destroy(true);
            },

        });
    },
});


});