(function() {
    'use strict';
    var website = openerp.website;
    website.openerp_website = {};

    website.snippet.options.ehtml = website.snippet.Option.extend({
        drop_and_build_snippet: function() {

        }

    })


    website.snippet.options.ehtml_field = website.snippet.Option.extend({
        drop_and_build_snippet: function() {


            var self = this;
            return website.prompt({
                id: "editor_field_options_button",
                window_title: "Edit Field Options",
            }).then(function (ehtml_id) {
                alert("edit");
                //self.$target.attr("data-id", mail_group_id);

            });


        }

    })




})();