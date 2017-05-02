odoo.define('web.web_widget_color', function(require) {
"use strict";

    var core = require('web.core');
    var widget = require('web.form_widgets');
    var FormView = require('web.FormView');

    var QWeb = core.qweb;

    var FieldAmor = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        template: 'FieldAmor',
init: function(field_manager, node) {
	alert("init");
},
        query_values: function() {
			alert("query values");
            var self = this;

            var model = new Model('migration.import.odbc.table.field');
            def = model.call("get_field_records", ['', this.get("domain")], {"context": this.build_context()});

            this.records_orderer.add(def).then(function(values) {
                if (! _.isEqual(values, self.get("values"))) {
                     self.set("values", values);
                }
            });
        },
        render_value: function () {
            if (!this.get("effective_readonly")) {
		        this.$el.html("<span style='text-decoration: underline;'>" + this.get("value") + "</span>");
		    } else {
                this.$("input").val(this.get("value"));
            }
        }
    });

    core.form_widget_registry.add('amor', FieldAmor);

    return {
        FieldAmor: FieldAmor
    };

});
