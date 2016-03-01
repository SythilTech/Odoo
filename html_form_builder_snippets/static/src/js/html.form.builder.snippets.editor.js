odoo.define('html_form_builder_snippets.editor', function (require) {
'use strict';

var Model = require('web.Model');
var base = require('web_editor.base');
var options = require('web_editor.snippets.options');
var session = require('web.session');
var website = require('website.website');

options.registry.html_form_builder = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;
        var model = new Model('html.form');
	    model.call('name_search', [], { context: base.get_context() }).then(function (form_ids) {

	        website.prompt({
			    id: "editor_new_form",
			    window_title: "New HTML Form",
			    select: "Select Form",
			    init: function (field) {
			        return form_ids;
			    },
			}).then(function (form_id) {

			    session.rpc('/form/load', {'form_id': form_id}).then(function(result) {
				    self.$target.html(result.html_string);
				    self.$target.attr('data-form-model', result.form_model );
				    self.$target.attr('data-form-id', form_id );
             	});
			});

        });
    },

});


options.registry.html_form_builder_field = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;
        var model = new Model('ir.model.fields');
        var form_id = this.$target.parents().closest(".html_form").attr('data-form-id')
        var form_model = this.$target.parents().closest(".html_form").attr('data-form-model')

	    model.call('name_search', ['', [["model_id.model", "=", form_model]] ], { context: base.get_context() }).then(function (field_ids) {

	        website.prompt({
			    id: "editor_new_field",
			    window_title: "New HTML Field",
			    select: "Select ORM Field",
			    init: function (field) {
			        return field_ids;
			    },
			}).then(function (field_id) {

			    session.rpc('/form/field/add', {'form_id': form_id, 'field_id': field_id, 'html_type': self.$target.attr('data-form-type') }).then(function(result) {
				    self.$target.html(result.html_string);
             	});
			});

        });

    },
});



});