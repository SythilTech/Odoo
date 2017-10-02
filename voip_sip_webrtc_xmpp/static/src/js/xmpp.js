odoo.define('voip_sip_webrtc_xmpp.xmpp_widget', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var Model = require('web.DataModel');
var session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var bus = require('bus.bus').bus;
var WebClient = require('web.WebClient');
var SystrayMenu = require('web.SystrayMenu');
var form_common = require('web.form_common');
var form_widgets = require('web.form_widgets');

var _t = core._t;
var qweb = core.qweb;

var FieldXMPP = form_widgets.FieldChar.extend({
    events: {
        'click .xmpp-message': 'start_xmpp_message',
    },
    render_value: function() {
        if (this.get("effective_readonly")) {
		    this.$el.html("" + this.get("value") + " <br/><a href=\"javascript:;\"class=\"fa fa-comments xmpp-message\" style=\"text-decoration: underline;\" aria-hidden=\"true\"> Message</a>");
        } else {
			this.$input.val(this.get("value"));
        }
    },
    start_xmpp_message: function() {

        console.log("Message Type: XMPP");

        var self = this;

        this.do_action({
            type: 'ir.actions.act_window',
            name: "Send Jabber Message",
            res_model: 'voip.message.compose',
            context: {'default_partner_id': this.getParent().get_fields_values()['id'], 'default_type': "xmpp"},
            views: [[false, 'form']],
            target: 'new'
        });
    }
});

core.form_widget_registry.add('xmpp', FieldXMPP)


});