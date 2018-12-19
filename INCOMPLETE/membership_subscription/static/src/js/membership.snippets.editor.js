odoo.define('membership.form.editor', function (require) {
'use strict';

var base = require('web_editor.base');
var options = require('web_editor.snippets.options');
var core = require('web.core');
var session = require('web.session');
var website = require('website.website');
var ajax = require('web.ajax');
var qweb = core.qweb;
var wUtils = require('website.utils');
var rpc = require('web.rpc');
var weContext = require('web_editor.context');

options.registry.membership_form = options.Class.extend({
    onBuilt: function() {
        var self = this;


        rpc.query({
                model: 'payment.membership',
                method: 'name_search',
                args: [],
                context: weContext.get()
            }).then(function(form_ids){

	            wUtils.prompt({
			        id: "editor_new_membership_form",
			        window_title: "Choose Membership Form",
			        select: "Select Form",
			        init: function (field) {
			            return form_ids;
			        },
			    }).then(function (form_id) {

			        session.rpc('/membership/form/load', {'form_id': form_id}).then(function(result) {
						self.$target.find("input[name='membership_id']").val(result.form_id);
                 	});
			    });

            });

    },
    cleanForSave: function () {
		var self = this;
		//Sometimes the form gets saved with the token in it
        self.$target.find("input[name='csrf_token']").attr("t-att-value","request.csrf_token()");
    },
});

});