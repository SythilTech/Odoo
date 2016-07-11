odoo.define('form_image_preview.image_widget_extend', function (require) {
"use strict";


    var core = require('web.core');
    var form_common = require('web.form_common');
    var imageWidget = core.form_widget_registry.get('image');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;

imageWidget.include({
    render_value: function() {
        var self = this;
        var url;
        this.session = session;
        if (this.get('value') && !utils.is_bin_size(this.get('value'))) {
            url = 'data:image/png;base64,' + this.get('value');
        } else if (this.get('value')) {
            var id = JSON.stringify(this.view.datarecord.id || null);
            var field = this.name;
            if (this.options.preview_image)
                field = this.options.preview_image;
            url = session.url('/web/image', {
                                        model: this.view.dataset.model,
                                        id: id,
                                        field: field,
                                        unique: (this.view.datarecord.__last_update || '').replace(/[^0-9]/g, ''),
            });
        } else {
            url = this.placeholder;
        }

        var record_id = this.getParent().get_fields_values()['id'];
        var current_model = this.getParent().model;
        var $img = $(QWeb.render("FieldBinaryImage-img", { widget: this, url: url }));
        $($img).click(function(e) {
            if(self.view.get("actual_mode") == "view") {

                var $button = $(".oe_form_button_edit");
                $button.openerpBounce();
                e.stopPropagation();
		        window.location.href = "/web/image/" + current_model + "/" + record_id + "/image"
            }
        });
        this.$el.find('> img').remove();
        this.$el.prepend($img);
        $img.load(function() {
            if (! self.options.size)
                return;
            $img.css("max-width", "" + self.options.size[0] + "px");
            $img.css("max-height", "" + self.options.size[1] + "px");
        });
        $img.on('error', function() {
            self.on_clear();
            $img.attr('src', self.placeholder);
            self.do_warn(_t("Image"), _t("Could not display the selected image."));
        });
    },

});


});