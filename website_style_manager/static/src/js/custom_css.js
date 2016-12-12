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

ajax.loadXML('/website_style_manager/static/src/xml/website_style_templates4.xml', qweb);

    contentMenu.TopBar.include({
        CustomCSSView: function() {

    		var self = this;

    		this.template = 'website_style_manager.custom_css_modal';
    		self.$modal = $( qweb.render(this.template, {}) );

    		$('body').append(self.$modal);

			session.rpc('/style/load', {}).then(function(result) {
			    self.$modal.find("#css_tags_tab").html(result.html_string)
			    self.$modal.find("#custom_css_text").val(result.custom_css)
            });

            $('#oe_webpage_custom_css_modal').modal('show');

            $('body').on('click', '#submit_custom_css', function() {
			    var page_template = $(this).data('template');
			    var page_name = $("#sythil_page_name").val();
				session.rpc('/styles/save', {'template_id': page_template, 'page_name': page_name}).then(function(result) {
				    //redirect to new page
					window.location.href = "/page/" + result.page_name;
				});

            });

        },
    });


});