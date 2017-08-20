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
var qweb = core.qweb;

ajax.loadXML('/website_template_pages/static/src/xml/website_template_pages_modal99.xml', qweb);

    contentMenu.TopBar.include({
        new_sythil_webpage: function() {

    		var self = this;

    		this.template = 'website_template_pages.pick_template_modal';
    		self.$modal = $( qweb.render(this.template, {}) );

    		$('body').append(self.$modal);

			session.rpc('/template/pages', {}).then(function(result) {
			    self.$modal.find("#templates_div").html(result.html_string)
            });

            $('#oe_webpage_template_modal').modal('show');

            $('body').on('click', '.page_template_glass_overlay', function() {
			    var page_template = $(this).data('template');

                //Deselect the cuurent one
                $(".page_template_glass_overlay").removeClass("page_template_glass_overlay_selected");

                $(this).addClass('page_template_glass_overlay_selected');
                $("#sythil_selected_template_id").val(page_template);

            });

            $('body').on('click', '#submit_webpage_template', function() {
			    var page_template = $("#sythil_selected_template_id").val();


			    var page_name = $("#sythil_page_name").val();
				session.rpc('/template/pages/new', {'template_id': page_template, 'page_name': page_name}).then(function(result) {
				    //redirect to new page
					window.location.href = "/page/" + result.page_name;
				});

            });

            $('body').on('click', '#template_online_tab', function() {

				session.rpc('/template/pages/sync/client', {}).then(function(result) {
			        self.$modal.find("#templates_div_online").html(result.html_string)
				});

            });

        },
        save_sythil_webpage: function() {
            var view_id = $(document.documentElement).data('view-xmlid');
			session.rpc('/template/pages/save', {'view_id': view_id}).then(function(result) {
			    if (result.code == "good") {
				    alert("Template Saved");
			    }
			});

	    },
    });


});
