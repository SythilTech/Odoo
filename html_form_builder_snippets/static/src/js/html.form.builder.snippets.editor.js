odoo.define('html_form_builder_snippets.editor', function (require) {
'use strict';

var Model = require('web.Model');
var base = require('web_editor.base');
var options = require('web_editor.snippets.options');
var session = require('web.session');
var website = require('website.website');
var return_string = ""; //Global because I can't change html in session.rpc function

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


	    model.call('name_search', ['', [["model_id.model", "=", form_model],["ttype", "=", field_type],["name", "!=", "display_name"] ] ], { context: base.get_context() }).then(function (field_ids) {

	        website.prompt({
			    id: "editor_new_field",
			    window_title: "New HTML Field",
			    select: "Select ORM Field",
			    init: function (field) {

                    var $group = this.$dialog.find("div.form-group");
                    $group.removeClass("mb0");

                    var $add = $(
                    '<div class="form-group">'+
                        '<label class="col-sm-3 control-label">Format Validation</label>'+
                        '<div class="col-sm-9">'+
                        '  <select name="formatValidation" class="form-control" required="required"> '+
                        '    <option value="">None</option>'+
                        '    <option value="email">Email</option>'+
                        '    <option value="lettersonly">Letters Only</option>'+
                        '  </select>'+
                        '</div>'+
                    '</div>'+
                    '<div class="form-group mb0">'+
                        '<label class="col-sm-3 control-label">Character Limit</label>'+
                        '<div class="col-sm-9">'+
                        '  <input type="number" name="characterLimit" class="form-control" value="100"/>'+
                        '</div>'+
                    '</div>');
                    //$add.find('label').append(_t("Add page in menu"));
                    $group.after($add);

			        return field_ids;
			    },
			}).then(function (val, field_id, $dialog) {
                var format_validation = $dialog.find('select[name="formatValidation"]').val();
                var character_limit = $dialog.find('input[name="characterLimit"]').val();

                session.rpc('/form/field/add', {'form_id': form_id, 'field_id': val, 'html_type': self.$target.attr('data-form-type'), 'format_validation': format_validation, 'character_limit': character_limit }).then(function(result) {
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

                    var $group = this.$dialog.find("div.form-group");
                    $group.removeClass("mb0");

                    var $add = $(
                    '<div class="form-group">'+
                        '<label class="col-sm-3 control-label">Client Key</label>'+
                        '<div class="col-sm-9">'+
                        '  <input type="text" name="clientKey" class="form-control"/>'+
                        '</div>'+
                    '</div>'+
                    '<div class="form-group mb0">'+
                        '<label class="col-sm-3 control-label">Client Secret</label>'+
                        '<div class="col-sm-9">'+
                        '  <input type="text" name="clientSecret" class="form-control"/>'+
                        '</div>'+
                    '</div>');
                    $group.after($add);

			        return captcha_ids;
			    },
			}).then(function (val, captcha_ids, $dialog) {

                var client_key = $dialog.find('input[name="clientKey"]').val();
                var client_secret = $dialog.find('input[name="clientSecret"]').val();

			    session.rpc('/form/captcha/load', {'captcha_id': val, 'form_id': form_id, 'client_key': client_key, 'client_secret':client_secret}).then(function(result) {
					self.$target.attr('data-captcha-id', val );
				    self.$target.html(result.html_string);
             	});

			});

        });
    },
    clean_for_save: function () {
        this._super();
        var self = this;

		var captcha_id = this.$target.attr('data-captcha-id');

        var form_id = $(".html_form_captcha").parents().closest(".html_form").attr('data-form-id');

	    session.rpc('/form/captcha/load', {'captcha_id': captcha_id, 'form_id': form_id}).done(function(result) {
		    self.$target.attr('data-captcha-id', captcha_id );
		    return_string = result.html_string;
            $(".html_form_captcha").html(return_string);
        });

        alert("Recaptcha Regenerated"); //Hate to do this but can't get it to call sync rather then async...
        $(".html_form_captcha").html(return_string);

    },
});


});