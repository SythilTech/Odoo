openerp.sms_frame = function (instance, local){
var _t = instance.web._t,
        _lt = instance.web._lt;
var QWeb = instance.web.qweb;

local.FieldChar2 = instance.web.form.AbstractField.extend({

    init: function() {
		this._super.apply(this, arguments);
        this.set("value", "");
    },

    start: function() {
        this.on("change:effective_readonly", this, function() {

            this.display_field();
            this.render_value();
        });
        this.display_field();
        return this._super();
    },
    display_field: function() {
        var self = this;
        this.$el.html(QWeb.render("sms_widget", {widget: this}));
        if (! this.get("effective_readonly")) {
            this.$("input").change(function() {
                self.internal_set_value(self.$("input").val());
            });
        }
    },
    render_value: function() {
        if (this.get("effective_readonly")) {
		    this.$el.html("<span style='text-decoration: underline;'>" + this.get("value") + "</span>");
        } else {
            this.$("input").val(this.get("value"));
        }
    },

    events: {
	    'click':'item_click',
	},

	item_click:function (ev) {
				ev.preventDefault();
				ev.stopPropagation();

                if (this.get("effective_readonly")) {

			        this.do_action({
	                    type:'ir.actions.act_window',
	                    res_model:'sms.compose',
	                    views: [[false,'form']],
	                    target:'new',
	                    context: {'default_field_id':this.name,'default_to_number':this.get("value"),'default_record_id':this.getParent().get_fields_values()['id'],'default_model_id':this.getParent().model},
                        });

			    }
		},


});

instance.web.form.widgets.add('sms_frame', 'instance.sms_frame.FieldChar2');





};