(function() {
    'use strict';
    var website = openerp.website;
    website.openerp_website = {};

    website.add_template_file('/html_form_maker/static/src/xml/html_form_modal8.xml');

    website.snippet.options.html_form_settings = website.snippet.Option.extend({
        drop_and_build_snippet: function() {
            var self = this;
            self.change_form_settings();
        },

        change_form_settings: function() {
            var self = this;

            self.$modal = $(openerp.qweb.render("html_form_maker.html_form_config_modal"));
            self.$modal.appendTo('body');
            self.$modal.modal();

		    $("#html_form_config_name").val(self.$target.find('h2').html() );
		    $("#html_form_config_return_url").val(self.$target.attr('data-form-return-url') );
		    $("#html_form_config_model").val(self.$target.attr('data-form-model') );


            self.$modal.find("#save_form").on('click', function () {
				//Save form name
				self.$target.find('h2').html( $("#html_form_config_name").val() );

				//save return url
				self.$target.attr('data-form-return-url', $("#html_form_config_return_url").val() );

				//save the ORM model
				self.$target.attr('data-form-model', $("#html_form_config_model").val() );

				var s = new openerp.Session();
				s.rpc('/form/updateform', {'form_id': self.$target.attr('data-form-id'),'name': $("#html_form_config_name").val(), 'return_url': $("#html_form_config_return_url").val(), 'model_id': $("#html_form_config_model").val() }).then(function(result) {
                    self.$target.attr('data-form-id', result);
                    self.$target.find('input[name=form_id]').val(result);

				});

                self.$modal.modal('hide');
            });

        },

        start : function () {
            var self = this;
            this.$el.find(".js_form_settings").on("click", _.bind(this.change_form_settings, this));
            this._super();
        },




    })


    website.snippet.options.html_form_field_settings = website.snippet.Option.extend({
        drop_and_build_snippet: function() {
            var self = this;
            self.change_field_settings();
        },

        on_remove: function () {
			var self = this;
	        var s = new openerp.Session();
			s.rpc('/form/deletefield', {'html_field_id': self.$target.attr('data-field-id') }).then(function(result) {

			});
        },

        change_field_settings: function() {
            var self = this;

            self.$modal = $(openerp.qweb.render("html_form_maker.html_form_field_config_modal"));
            self.$modal.appendTo('body');
            self.$modal.modal();

            var field_id = 0;

            //Find the parent form
            $("#html_form_id").val( self.$target.parents().find(".ehtml_form").attr('data-form-id') );

		    self.$modal.find("#html_form_config_label").val(self.$target.find('label').html() );

            $(document).ready(function() {
                $("#html_form_config_field").autocomplete({
                    source: '/form/getfields?html_type=' + self.$target.attr('data-form-type'),
                    minLength: 1,
                    select: function( event, ui ) {
		    			$("#html_form_config_label").val(ui.item.description);
		    			$("#html_form_field_config_name").val(ui.item.value);
		    			field_id = ui.item.id;
                    }
                });

            });


            self.$modal.find("#save_field").on('click', function () {
				self.$target.find('label').html(self.$modal.find("#html_form_config_label").val());
				self.$target.find('label').attr('for', self.$modal.find("#html_form_config_name").val() );
				self.$target.find('input').attr("name", self.$modal.find("#html_form_field_config_name").val() );

				var s = new openerp.Session();
				s.rpc('/form/updatefield', {'form_id': self.$target.parents().find(".ehtml_form").attr('data-form-id'), 'html_field_id': self.$target.attr('data-field-id'), 'field': field_id, 'field_type': self.$target.attr('data-form-type'), 'html_name': self.$modal.find("#html_form_field_config_name").val(), 'label': self.$modal.find("#html_form_config_label").val() }).then(function(result) {
                    self.$target.attr('data-field-id', result.field_id);
                    self.$target.html(result.html);

				});

                self.$modal.modal('hide');
            });

        },

        start : function () {
            var self = this;
            this.$el.find(".js_form_field_settings").on("click", _.bind(this.change_field_settings, this));
            this._super();
        },

    })




})();