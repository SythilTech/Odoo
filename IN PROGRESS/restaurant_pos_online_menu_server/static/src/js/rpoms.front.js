$(document).ready(function() {
    $("#takeaway_search").autocomplete({
        source: '/takeaway/search/autocomplete',
        minLength: 1,
        select: function( event, ui ) {
            window.location.href = ui.item.value;
        }
    });
});