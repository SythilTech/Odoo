odoo.define('html_form_builder_snippets.editor', function (require) {
'use strict';

var Model = require('web.Model');
var base = require('web_editor.base');
var options = require('web_editor.snippets.options');
var core = require('web.core');
var session = require('web.session');
var website = require('website.website');
var return_string = ""; //Global because I can't change html in session.rpc function
var ajax = require('web.ajax');
var qweb = core.qweb;

ajax.loadXML('/html_form_builder_snippets/static/src/xml/html_form_modal16.xml', qweb);

$(function() {
  $( ".html_form button" ).click(function(e) {

    e.preventDefault();  // Prevent the default submit behavior

    var my_form = $(".html_form form");

    // Prepare form inputs
    var form_data = my_form.serializeArray();

     var form_values = {};
            _.each(form_data, function(input) {
                if (input.name in form_values) {
                    // If a value already exists for this field,
                    // we are facing a x2many field, so we store
                    // the values in an array.
                    if (Array.isArray(form_values[input.name])) {
                        form_values[input.name].push(input.value);
                    } else {
                        form_values[input.name] = [form_values[input.name], input.value];
                    }
                } else {
                    if (input.value != '') {
                        form_values[input.name] = input.value;
                    }
                }
            });

    form_values['is_ajax_post'] = "Yes";

    // Post form and handle result
    ajax.post(my_form.attr('action'), form_values).then(function(result_data) {
      result_data = $.parseJSON(result_data);
      if (result_data.status == "error") {
        for (var i = 0; i < result_data.errors.length; i++) {
		  //Find the field and make it displays as an error
          var input = my_form.find("input[name='" + result_data.errors[i].html_name + "']");
          var parent_div = input.parent("div");

          //Remove any existing help block
          parent_div.find(".help-block").remove();

          //Insert help block
          input.after("<span class=\"help-block\">" + result_data.errors[i].error_messsage + "</span>");
          parent_div.addClass("has-error");
        }
      } else if (result_data.status == "success") {
	      window.location = result_data.redirect_url;
      }
    });

  });
});

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

// ------------------------ TEXTBOX CONFIG ----------------------
options.registry.html_form_builder_field_textbox = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;

    	this.template = 'html_form_builder_snippets.textbox_config';
    	self.$modal = $( qweb.render(this.template, {}) );

        //Remove previous instance first
        $('#htmlTextboxModal').remove();

    	$('body').append(self.$modal);
    	var datatype_dict = ['char'];
        var form_model = this.$target.parents().closest(".html_form").attr('data-form-model')
        var form_id = this.$target.parents().closest(".html_form").attr('data-form-id')

        //Count the amount of bootstrap columns in the row
        var current_columns = 0;
        if (self.$target.parent().attr("id") == "html_field_placeholder") {
            self.$target.parent().parent().find(".hff").each(function( index ) {
	    	    if ($( this ).hasClass("col-md-12")) { current_columns = 12;}
	    		if ($( this ).hasClass("col-md-11")) { current_columns = 11;}
	    		if ($( this ).hasClass("col-md-10")) { current_columns = 10;}
	    		if ($( this ).hasClass("col-md-9")) { current_columns = 9;}
	    		if ($( this ).hasClass("col-md-8")) { current_columns = 8;}
	    		if ($( this ).hasClass("col-md-7")) { current_columns = 7;}
	    		if ($( this ).hasClass("col-md-6")) { current_columns = 6;}
	    		if ($( this ).hasClass("col-md-5")) { current_columns = 5;}
	    		if ($( this ).hasClass("col-md-4")) { current_columns = 4;}
	    		if ($( this ).hasClass("col-md-3")) { current_columns = 3;}
	    		if ($( this ).hasClass("col-md-2")) { current_columns = 2;}
	    		if ($( this ).hasClass("col-md-1")) { current_columns = 1;}
            });
	    }

        //Only show sizes that that are less then or equal to the remiaining columns
        var field_size_html = "";
        var i = 0;
        for (i = (12 - current_columns); i > 0; i--) {
			var number = (i / 12 * 100);
            field_size_html += "<option value=\"" + i + "\">" + Math.round( number * 10 ) / 10 + "%</option>\n"
		}

        self.$modal.find('#field_size').html(field_size_html);

		session.rpc('/form/field/config/general', {'data_types':datatype_dict, 'form_model':form_model}).then(function(result) {
		    self.$modal.find("#field_config_id").html(result.field_options_html);
        });

        $('#htmlTextboxModal').modal('show');

        $('body').on('click', '#save_textbox_field', function() {
            var field_id = self.$modal.find('#field_config_id').val();
            if (field_id != "") {
	            var format_validation = self.$modal.find('#html_form_field_format_validation').val();
                var character_limit = self.$modal.find('#html_form_field_character_limit').val();
                var field_required = self.$modal.find('#html_form_field_required').is(':checked');
                var field_size = self.$modal.find('#field_size').val();

                session.rpc('/form/field/add', {'form_id': form_id, 'field_id': field_id, 'html_type': self.$target.attr('data-form-type'), 'format_validation': format_validation, 'character_limit': character_limit, 'field_required': field_required }).then(function(result) {
		    	    if (field_size == "12") {
		    	        self.$target.replaceWith(result.html_string);
				    } else {
						var header_wrapper = "";
						var footer_wrapper = "";

					    //Create a row if you are the first element in a "row" of fields
						if (self.$target.parent().attr("id") == "html_fields") {
						    header_wrapper = "<div class=\"row\">\n";
						    footer_wrapper = "</div>";
						}

						//Remove the placeholder div to keep the HTML clean
                        if (self.$target.parent().attr("id") == "html_field_placeholder") {
	  	    	            self.$target.unwrap();
						}

                        //Add the current field size otherwise the reminaing wwhile be off
                        current_columns += field_size;

                        var remaining_columns = 12 - current_columns;

                        if (remaining_columns > 0) {
                            footer_wrapper = "<div id=\"html_field_placeholder\" data-field-size=\"" + remaining_columns + "\" class=\"col-md-" + remaining_columns + "\"/>\n" + footer_wrapper;
					    }

					    self.$target.replaceWith(header_wrapper + result.html_string.replace("hff ","hff col-md-" + field_size + " ") + footer_wrapper);


					}
                });

                $('#htmlTextboxModal').modal('hide');

		    }

        });

    },
});

// ------------------------ TEXTAREA CONFIG ----------------------
options.registry.html_form_builder_field_textarea = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;

    	this.template = 'html_form_builder_snippets.textarea_config';
    	self.$modal = $( qweb.render(this.template, {}) );

        //Remove previous instance first
        $('#htmlTextareaModal').remove();

    	$('body').append(self.$modal);
    	var datatype_dict = ['text'];
        var form_model = this.$target.parents().closest(".html_form").attr('data-form-model')
        var form_id = this.$target.parents().closest(".html_form").attr('data-form-id')

        //Count the amount of bootstrap columns in the row
        var current_columns = 0;
        if (self.$target.parent().attr("id") == "html_field_placeholder") {
            self.$target.parent().parent().find(".hff").each(function( index ) {
	    	    if ($( this ).hasClass("col-md-12")) { current_columns = 12;}
	    		if ($( this ).hasClass("col-md-11")) { current_columns = 11;}
	    		if ($( this ).hasClass("col-md-10")) { current_columns = 10;}
	    		if ($( this ).hasClass("col-md-9")) { current_columns = 9;}
	    		if ($( this ).hasClass("col-md-8")) { current_columns = 8;}
	    		if ($( this ).hasClass("col-md-7")) { current_columns = 7;}
	    		if ($( this ).hasClass("col-md-6")) { current_columns = 6;}
	    		if ($( this ).hasClass("col-md-5")) { current_columns = 5;}
	    		if ($( this ).hasClass("col-md-4")) { current_columns = 4;}
	    		if ($( this ).hasClass("col-md-3")) { current_columns = 3;}
	    		if ($( this ).hasClass("col-md-2")) { current_columns = 2;}
	    		if ($( this ).hasClass("col-md-1")) { current_columns = 1;}
            });
	    }

        //Only show sizes that that are less then or equal to the remiaining columns
        var field_size_html = "";
        var i = 0;
        for (i = (12 - current_columns); i > 0; i--) {
			var number = (i / 12 * 100);
            field_size_html += "<option value=\"" + i + "\">" + Math.round( number * 10 ) / 10 + "%</option>\n"
		}

        self.$modal.find('#field_size').html(field_size_html);

		session.rpc('/form/field/config/general', {'data_types':datatype_dict, 'form_model':form_model}).then(function(result) {
		    self.$modal.find("#field_config_id").html(result.field_options_html);
        });

        $('#htmlTextareaModal').modal('show');

        $('body').on('click', '#save_textarea_field', function() {
            var field_id = self.$modal.find('#field_config_id').val();
            if (field_id != "") {
                var field_required = self.$modal.find('#html_form_field_required').is(':checked');
                var field_size = self.$modal.find('#field_size').val();

                session.rpc('/form/field/add', {'form_id': form_id, 'field_id': field_id, 'html_type': self.$target.attr('data-form-type'), 'field_required': field_required }).then(function(result) {
		    	    if (field_size == "12") {
		    	        self.$target.replaceWith(result.html_string);
				    } else {
						var header_wrapper = "";
						var footer_wrapper = "";

					    //Create a row if you are the first element in a "row" of fields
						if (self.$target.parent().attr("id") == "html_fields") {
						    header_wrapper = "<div class=\"row\">\n";
						    footer_wrapper = "</div>";
						}

						//Remove the placeholder div to keep the HTML clean
                        if (self.$target.parent().attr("id") == "html_field_placeholder") {
	  	    	            self.$target.unwrap();
						}

                        //Add the current field size otherwise the reminaing wwhile be off
                        current_columns += field_size;

                        var remaining_columns = 12 - current_columns;

                        if (remaining_columns > 0) {
                            footer_wrapper = "<div id=\"html_field_placeholder\" data-field-size=\"" + remaining_columns + "\" class=\"col-md-" + remaining_columns + "\"/>\n" + footer_wrapper;
					    }

					    self.$target.replaceWith(header_wrapper + result.html_string.replace("hff ","hff col-md-" + field_size + " ") + footer_wrapper);


					}
                });

                $('#htmlTextareaModal').modal('hide');

		    }

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
                    '<div class="form-group">'+
                        '<label class="col-sm-3 control-label">Character Limit</label>'+
                        '<div class="col-sm-9">'+
                        '  <input type="number" name="characterLimit" class="form-control" value="100"/>'+
                        '</div>'+
                    '</div>'+
                    '<div class="checkbox mb0">'+
                        '<label><input type="checkbox" name="form_required_checkbox">Required</label>'+
                    '</div>'
                    );
                    $group.after($add);

			        return field_ids;
			    },
			}).then(function (val, field_id, $dialog) {
                var format_validation = $dialog.find('select[name="formatValidation"]').val();
                var character_limit = $dialog.find('input[name="characterLimit"]').val();
                var field_required = $dialog.find('input[name="form_required_checkbox"]').is(':checked');

                session.rpc('/form/field/add', {'form_id': form_id, 'field_id': val, 'html_type': self.$target.attr('data-form-type'), 'format_validation': format_validation, 'character_limit': character_limit, 'field_required': field_required }).then(function(result) {
				    self.$target.replaceWith(result.html_string);
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