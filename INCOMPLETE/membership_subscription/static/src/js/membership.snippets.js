odoo.define('membership.form.front', function (require) {
'use strict';

var base = require('web_editor.base');
var core = require('web.core');
var session = require('web.session');
var website = require('website.website');
var ajax = require('web.ajax');
var qweb = core.qweb;
var wUtils = require('website.utils');
var rpc = require('web.rpc');
var weContext = require('web_editor.context');

$(function() {

    $(".btn-website-membership-signup").click(function(e) {

		e.preventDefault();  // Prevent the default submit behavior

		var my_form = $("form");

		// Prepare form inputs
        var form_data = my_form.serializeArray();

        var form_values = {};
        _.each(form_data, function(input) {
            if (input.value != '') {
                form_values[input.name] = input.value;
            }
        });

        ajax.post('/membership/signup/process', form_values).then(function(result) {
            if (result) {
				var result_data = $.parseJSON(result);
                if (result_data.status == "paid") {
                    window.location = result_data.redirect_url;
                } else if (result_data.status == "unpaid") {
                    ajax.jsonRpc('/shop/payment/transaction', 'call', {
                        'acquirer_id': result_data.acquirer,
                        'save_token': true,
                    }).then(function (result) {
                        if (result) {
                            // if the server sent us the html form, we create a form element
                            var newForm = document.createElement('form');
                            newForm.setAttribute("method", "post"); // set it to post
                            //newForm.setAttribute("provider", checked_radio.dataset.provider);
                            newForm.hidden = true; // hide it
                            newForm.innerHTML = result; // put the html sent by the server inside the form
                            var action_url = $(newForm).find('input[name="data_set"]').data('actionUrl');
                            newForm.setAttribute("action", action_url); // set the action url
                            $(document.getElementsByTagName('body')[0]).append(newForm); // append the form to the body
                            $(newForm).find('input[data-remove-me]').remove(); // remove all the input that should be removed
                            if(action_url) {
                                newForm.submit(); // and finally submit the form
                            }
                        } else {
                            alert("We are not able to redirect you to the payment form.");
                        }
                    }).fail(function (message, data) {
                        alert("We are not able to redirect you to the payment form.</p>" + (core.debug ? data.data.message : ''));
                    });
			    }
		    }
        });
    });
});

});