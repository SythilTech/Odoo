odoo.define('csv_import_upload_migrate.ProgressWindow', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;


var ProgressWindow = Widget.extend({
    template: "csv_import_upload_migrate.ProgressWindow",

    init: function(parent, action) {
		console.log("init");
        this._super(parent, action);
    },

});
/*
$( document ).ready(function() {
    this.progress_window = new ProgressWindow();
    $('body').append(this.progress_window);
});
*/
});