odoo.define('sythil_theme', function (require) {
'use strict';

var Model = require('web.Model');
var ajax = require('web.ajax');
var core = require('web.core');
var base = require('web_editor.base');
var web_editor = require('web_editor.editor');
var options = require('web_editor.snippets.options');
var snippet_editor = require('web_editor.snippet.editor');
var session = require('web.session');
var website = require('website.website');
var _t = core._t;
var Widget = require('web.Widget');
var contentMenu = require('website.contentMenu');
var websiteAce = require('website.ace');
var qweb = core.qweb;

ajax.loadXML('/website_style_manager/static/src/xml/website_style_templates3.xml', qweb);

var CustomCSSEditor = Widget.extend({
    template: 'website_style_manager.custom_css',
    events: {
		'click a[data-action=CustomCSSView]': 'launchCSS',
    },
    launchCSS: function (e) {
        var self = this;

    	this.template = 'website_style_manager.custom_css';
    	self.$modal = $( qweb.render(this.template, {}) );

        //Remove previous instance first
        $('#myCSSEditor').remove();

    	$('body').append(self.$modal);
        self.$modal.removeClass('oe_ccsse_closed').addClass('oe_ccsse_open');
	    session.rpc('/style/load', {}).then(function(result) {
		    $("#website-custom-css").html(result.css_string);
        });



    $("#saveCSS").click(function() {
	    session.rpc('/style/save', {'css': $("#website-custom-css").val() }).then(function(result) {
			alert("Save Complete");
		    $("#custom_css_header").html(result.css_string);
            $('#myCSSEditor').remove();
         });
    });

    $("#formatCSS").click(function() {
         alert("Format CSS");
    });

    $("#closeCSS").click(function() {
         $("#myCSSEditor").removeClass('oe_ccsse_open').addClass('oe_ccsse_closed');
         $('#myCSSEditor').remove();
    });

    $("#website-custom-css").on('change keyup paste', function() {
        $("#custom_css_header").html( $("#website-custom-css").val() );
    });

    },
});

website.TopBar.include({
    start: function () {
        this.ccsse = new CustomCSSEditor();
        return $.when(
            this._super.apply(this, arguments),
            this.ccsse.attachTo($('#sythil_custom_css'))
        );
    },
});

});