console.log("1");
odoo.define('sythil_saas_client.sythil_saas_client', function (require) {
"use strict";

console.log("2");
var core = require('web.core');
var framework = require('web.framework');
var Model = require('web.DataModel');
var session = require('web.session');
var web_client = require('web.web_client');
var Widget = require('web.Widget');

var _t = core._t;
var qweb = core.qweb;

var Apps = require('base.apps');

    var admin_only_app_store = Apps.include({
    get_client: function() {
		alert("Test");
		console.log("test");
        // return the client via a deferred, resolved or rejected depending if the remote host is available or not.
        var check_client_available = function(client) {
            var d = $.Deferred();
            var i = new Image();
            i.onerror = function() {
                d.reject(client);
            };
            i.onload = function() {
                d.resolve(client);
            };
            var ts = new Date().getTime();
            i.src = _.str.sprintf('%s/web/static/src/img/sep-a.gif?%s', client.origin, ts);
            return d.promise();
        };
        if (apps_client) {
            return check_client_available(apps_client);
        } else {
            var Mod = new Model('ir.module.module');
            return Mod.call('get_apps_server').then(function(u) {
                var link = $(_.str.sprintf('<a href="%s"></a>', u))[0];
                var host = _.str.sprintf('%s//%s', link.protocol, link.host);
                var dbname = link.pathname;
                if (dbname[0] === '/') {
                    dbname = dbname.substr(1);
                }
                var client = {
                    origin: host,
                    dbname: dbname
                };
                apps_client = client;
                return check_client_available(client);
            });
        }
    },

    });

});