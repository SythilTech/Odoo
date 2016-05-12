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
			    window_title: "Existing HTML Form",
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

options.registry.html_form_builder_new = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;
        var model = new Model('html.form.snippet.action');
	    model.call('name_search', [], { context: base.get_context() }).then(function (action_ids) {

	        website.prompt({
			    id: "editor_new_form_new",
			    window_title: "New HTML Form",
			    select: "Select Action",
			    init: function (field) {
			        return action_ids;
			    },
			}).then(function (action_id) {

			    session.rpc('/form/new', {'action_id': action_id}).then(function(result) {
				    self.$target.html(result.html_string);
				    self.$target.attr('data-form-model', result.form_model );
				    self.$target.attr('data-form-id', result.form_id );
				    //Behaves like a regular form after creation
				    self.$target.attr('class', 'html_form' );
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


	    session.rpc('/form/fieldtype', {'field_type': self.$target.attr('data-form-type') }).then(function(result) {
		    var field_type = result.field_type;




	    model.call('name_search', ['', [["model_id.model", "=", form_model],["ttype", "=", field_type] ] ], { context: base.get_context() }).then(function (field_ids) {

	        website.prompt({
			    id: "editor_new_field",
			    window_title: "New HTML Field",
			    select: "Select ORM Field",
			    init: function (field) {

                    var $group = this.$dialog.find("div.form-group");
                    $group.removeClass("mb0");

                    var $add = $(
                    '<div class="form-group mb0">'+
                        '<label class="col-sm-3 control-label">Format Validation</label>'+
                        '<div class="col-sm-9">'+
                        '  <select name="formatValidation" class="form-control" required="required"> '+
                        '    <option value="">None</option>'+
                        '    <option value="email">Email</option>'+
                        '    <option value="lettersonly">Letters Only</option>'+
                        '  </select>'+
                        '</div>'+
                    '</div>');
                    //$add.find('label').append(_t("Add page in menu"));
                    $group.after($add);

			        return field_ids;
			    },
			}).then(function (val, field_id, $dialog) {
                var format_validation = $dialog.find('select[name="formatValidation"]').val();

                session.rpc('/form/field/add', {'form_id': form_id, 'field_id': val, 'html_type': self.$target.attr('data-form-type'), 'format_validation': format_validation }).then(function(result) {
				    self.$target.html(result.html_string);
             	});
			});

        });


        });


    },
});



options.registry.html_form_builder_captcha = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;
        var model = new Model('html.form.captcha');
        var form_id = this.$target.parents().closest(".html_form").attr('data-form-id')

	    model.call('name_search', [], { context: base.get_context() }).then(function (captcha_ids) {

	        website.prompt({
			    id: "editor_new_captcha",
			    window_title: "New Captcha",
			    select: "Select Captcha Type",
			    init: function (field) {
			        return captcha_ids;
			    },
			}).then(function (captcha_id) {

			    session.rpc('/form/captcha/load', {'captcha_id': captcha_id, 'form_id': form_id}).then(function(result) {
				    self.$target.html(result.html_string);
             	});

			});

        });
    },

});


});