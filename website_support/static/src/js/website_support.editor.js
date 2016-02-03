odoo.define('website_support.new_help_page', function (require) {
"use strict";

    var core = require('web.core');
    var base = require('web_editor.base');
    var Model = require('web.Model');
    var website = require('website.website');
    var contentMenu = require('website.contentMenu');

    var _t = core._t;

    contentMenu.TopBar.include({
        new_help_page: function() {
          website.prompt({
                id: "editor_new_help_page",
                window_title: _t("New Help Page"),
                select: "Select Help Group",
                init: function (field) {
					var help_group = new Model('website.support.help.groups');
                    return help_group.call('name_search', [], { context: base.get_context() });
                },
            }).then(function (cat_id) {
                document.location = '/helppage/new?group_id=' + cat_id;
            });
        },
    });
});


odoo.define('website_support.new_help_page', function (require) {
"use strict";

    var core = require('web.core');
    var base = require('web_editor.base');
    var Model = require('web.Model');
    var website = require('website.website');
    var contentMenu = require('website.contentMenu');

    var _t = core._t;

    contentMenu.TopBar.include({
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