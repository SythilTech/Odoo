odoo.define('voip_sip_webrtc_website.editor', function (require) {
'use strict';

var Model = require('web.Model');
var base = require('web_editor.base');
var options = require('web_editor.snippets.options');
var core = require('web.core');
var session = require('web.session');
var website = require('website.website');
var ajax = require('web.ajax');
var qweb = core.qweb;

ajax.loadXML('/voip_sip_webrtc_website/static/src/xml/voip_call_button_modal.xml', qweb);

options.registry.voip_button = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;

    	this.template = 'voip_sip_webrtc_website.voipCallButtonModal';
    	self.$modal = $( qweb.render(this.template, {}) );

        //Remove previous instance first
        $('#voipCallButtonModal').remove();

    	$('body').append(self.$modal);

        /* Fetch a list of users that can be called */
		session.rpc('/voip/website/users', {}).then(function(result) {
		    self.$modal.find("#voip_call_user").html(result.user_list_html);
        });

        $('#voipCallButtonModal').modal('show');

        $('body').on('click', '#save_voip_button', function() {
            var user_id = self.$modal.find('#voip_call_user').val();
            if (user_id != "") {
				var button_url = window.location.href;
                session.rpc('/voip/website/button/add', {'user_id': user_id, 'url': button_url}).then(function(result) {
                    //Add the button id just incase we want to modify the button later
					self.$target.attr('data-voip-button-id', result.voip_button_id );
                    $('#voipCallButtonModal').modal('hide');
                });
		    }
        });

    },
});


});