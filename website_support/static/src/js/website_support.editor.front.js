$(document).ready(function() {
    $("#search_help_pages").autocomplete({
        source: '/support/help/auto-complete',
        minLength: 1,
        select: function( event, ui ) {
            window.location.href = ui.item.value;
        }
    });
});