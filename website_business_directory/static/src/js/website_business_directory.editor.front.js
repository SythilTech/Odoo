$(document).ready(function() {
    $("#search_business_directory").autocomplete({
        source: '/directory/auto-complete',
        minLength: 1,
        select: function( event, ui ) {
            window.location.href = ui.item.value;
        }
    }).data("ui-autocomplete")._renderItem = function (ul, item) {
         return $("<li></li>")
             .data("item.autocomplete", item)
             .append("<a>" + item.label + "</a>")
             .appendTo(ul);
    };
});