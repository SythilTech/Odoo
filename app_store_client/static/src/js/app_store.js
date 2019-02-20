odoo.define('app_store_client.custom_apps', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var session = require('web.session');
var Widget = require('web.Widget');
var rpc = require('web.rpc');

var _t = core._t;
var qweb = core.qweb;

//Get the app store url from parameters
var my_app_url = ""
rpc.query({
    model: 'ir.config_parameter',
    method: 'get_param',
    args: ['custom_app_store_url']
}).then(function(app_url){
	my_app_url = app_url;
    console.log(app_url);
});

window.onmessage = function(e){

    //Check origin matches app store url to make sure nothing weird is happening
    if (my_app_url == e.origin) {

		session.rpc('/appstore/module/download', {'module_name': e.data}).then(function(result) {
			alert("Module Installed");
        });

	} else {
		console.log("Origin Mismatch");
	}
};

var CustomApps = Widget.extend({
    template: 'app_store_client.app_store_iframe',
    remote_action_tag: 'loempia.embed',
    failback_action_id: 'base.open_module_tree',

    init: function(parent, action) {
        this._super(parent, action);
    },
    start: function() {
        var my_iframe = this.$el;
        my_iframe.css({height: '100%', width: '100%', border: 0});
        my_iframe.attr({src: my_app_url + "/client/apps"});

        return this._super();
    },

});

core.action_registry.add("custom_apps", CustomApps);

return CustomApps;

});
