$(document).ready(function() {
	var pos_menu_order = [];
    $(".pos-order-button").click(function() {
		var item_id = $(this).data('item-id');
		var item_name = $(this).data('item-name');
		var item_price = $(this).data('item-price');

        //Loop through existing order to find if it has been adde
        var found = false;
        for (var i = 0; i < pos_menu_order.length; i++) {
			if (pos_menu_order[i].id == item_id) {
			    found = true;
			    pos_menu_order[i].quantity += 1;
			}
		}

        if (found == false) {
            pos_menu_order.push({'id': item_id, 'name': item_name, 'price': item_price, 'quantity': 1})
		}

        $("#pos-order-panel").empty();

        //Loop through the orders and output them as HTML
        for (var i = 0; i < pos_menu_order.length; i++) {
			var item = pos_menu_order[i];
		    $("#pos-order-panel").append(item.name + " $" + item.price + " x" + item.quantity + "<br/>\n");
		}

    });
});