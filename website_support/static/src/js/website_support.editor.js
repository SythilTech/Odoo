$(document).ready(function() {
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;

    $(document).ready(function() {
        $("#search").autocomplete({
            source: '/support/help/auto-complete',
            minLength: 1,
            select: function( event, ui ) {
                window.location.href = ui.item.value;
            }
        });
    });

    website.EditorBarContent.include({
        new_help_page: function() {
          website.prompt({
                id: "editor_new_help_page",
                window_title: _t("New Help Page"),
                select: "Select Help Group",
                init: function (field) {
                    return website.session.model('website.support.help.groups')
                            .call('name_search', [], { context: website.get_context() });
                },
            }).then(function (cat_id) {
                document.location = '/helppage/new?group_id=' + cat_id;
            });
        },

        new_help_group: function() {
            website.prompt({
                id: "editor_new_help_group",
                window_title: _t("New Help Group"),
                input: _t("Help Group"),
                init: function () {

                }
            }).then(function (val, field, $dialog) {
                if (val) {
                    var url = '/helpgroup/new/' + encodeURIComponent(val);
                    document.location = url;
                }
            });
        },
    });
});
