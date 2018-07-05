odoo.define('voip_sip_webrtc.voip_system_tray', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var odoo_session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var bus = require('bus.bus').bus;
var Notification = require('web.notification').Notification;
var WebClient = require('web.WebClient');
var SystrayMenu = require('web.SystrayMenu');
var voip_notification = require('voip_sip_webrtc.voip_call_notification');
var rpc = require('web.rpc');
var weContext = require('web_editor.context');

var _t = core._t;
var qweb = core.qweb;

var VOIPSystemTray = Widget.extend({
    template:'VoipSystemTray',
    events: {
        "click": "on_click",
        "click .start_voip_audio_call": "start_voip_audio_call",
        "click .start_voip_video_call": "start_voip_video_call",
        "click .start_voip_screenshare_call": "start_voip_screenshare_call",
    },
    on_click: function (event) {
        event.preventDefault();

        rpc.query({
            model: 'voip.server',
            method: 'user_list',
            args: [],
            context: weContext.get()
        }).then(function(result){

            $("#voip_tray").html("");

            for (var voip_user in result) {
                var voip_user = result[voip_user];
                var drop_menu_html = "";

                drop_menu_html += "<li class=\"sy_phone_menu\">";
                drop_menu_html += voip_user.name +  " (" + voip_user.status + ")";

                if (voip_user.status == "Online") {
                    drop_menu_html += " <span style=\"float:right\"><i class=\"fa fa-volume-up start_voip_audio_call\" data-partner=\"" + voip_user.partner_id + "\" title=\"Audio Call\" aria-hidden=\"true\"/> <i class=\"fa fa-video-camera start_voip_video_call\" data-partner=\"" + voip_user.partner_id + "\" title=\"Video Call\" aria-hidden=\"true\"/> <i class=\"fa fa-desktop start_voip_screenshare_call\" data-partner=\"" + voip_user.partner_id + "\" title=\"Screen Sharing\" aria-hidden=\"true\"/></span>";
                }

                drop_menu_html += "</li>";

                $("#voip_tray").append(drop_menu_html);

            }

            if (result.length == 0) {
                $("#voip_tray").append("<span style=\"padding:10px;text-align:center;\">No connected users</span>");
            }

        });

    },
    start_voip_screenshare_call: function (event) {
        console.log("Call Type: screenshare call");

        var role = "caller";
        var mode = "screensharing";
        var call_type = "internal";
        var to_partner_id = $(event.currentTarget).data("partner");

        var voip_call_client = new voip_notification.VoipCallClient(role, mode, call_type, to_partner_id);

        var constraints = {'audio': true, 'video': {'mediaSource': "screen"}};
        voip_call_client.requestMediaAccess(constraints);

    },
    start_voip_audio_call: function (event) {
        console.log("Call Type: audio call");

        var role = "caller";
        var mode = "audiocall";
        var call_type = "internal";
        var to_partner_id = $(event.currentTarget).data("partner");

        var voip_call_client = new voip_notification.VoipCallClient(role, mode, call_type, to_partner_id);

        var constraints = {'audio': true};
        voip_call_client.requestMediaAccess(constraints);


    },
    start_voip_video_call: function (event) {
        console.log("Call Type: video call");

        var role = "caller";
        var mode = "videocall";
        var call_type = "internal";
        var to_partner_id = $(event.currentTarget).data("partner");

        var voip_call_client = new voip_notification.VoipCallClient(role, mode, call_type, to_partner_id);

        var constraints = {'audio': true, 'video': true};
        voip_call_client.requestMediaAccess(constraints);

    },
});

SystrayMenu.Items.push(VOIPSystemTray);

});