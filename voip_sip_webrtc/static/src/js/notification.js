odoo.define('voip_sip_webrtc.voip_call_notification', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var Model = require('web.DataModel');
var session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var ajax = require('web.ajax');

var _t = core._t;
var qweb = core.qweb;

var VOIPNotification = Widget.extend({
    template: 'voip_sip_webrtc.call_notification_popup',

    init: function(parent, action) {
        this._super(parent, action);
    },
    start: function() {
		alert("Answer the phone");
        return this._super();
    },

});

core.action_registry.add("voip_call_notification", VOIPNotification);

});
