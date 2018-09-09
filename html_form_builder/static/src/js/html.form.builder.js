odoo.define('html_form_builder.front', function (require) {
'use strict';

var ajax = require('web.ajax');

$(function() {

  //Load the token via javascript since Odoo has issue with request.csrf_token() inside snippets
  $(".html_form input[name='csrf_token']").val(odoo.csrf_token);

  $( ".html_form button.btn-lg" ).click(function(e) {

    e.preventDefault();  // Prevent the default submit behavior

    var my_form = $(".html_form form");

    $(".html_form form input").each(function( index ) {
        pattern = $( this ).attr('pattern');
		if (typeof pattern !== typeof undefined && pattern !== false) {
		    var pattern = new RegExp( pattern );
		    var valid = pattern.test( $( this ).val() );
		    //Why does this always return true?!?
		}

	});


    // Prepare form inputs
    var form_data = my_form.serializeArray();

    var form_values = {};
    _.each(form_data, function(input) {
        if (input.name in form_values) {
            // If a value already exists for this field,
            // we are facing a x2many field, so we store
            // the values in an array.
            if (Array.isArray(form_values[input.name])) {
                form_values[input.name].push(input.value);
            } else {
                form_values[input.name] = [form_values[input.name], input.value];
            }
        } else {
            if (input.value != '') {
                form_values[input.name] = input.value;
            }
        }
    });

    //Input groups are added differently
    var input_groups = my_form.find(".hff_input_group")
    input_groups.each(function( index ) {
      var html_name = $( this ).attr("data-html-name");
      var input_group_list = [];
      input_group_list = [];
      var row_string = "";
      var row_counter = 0;

      //Go through each row(exlcuding the add button row)
      var input_group_row = $( this ).find(".row.form-group")
      input_group_row.each(function( index ) {

		  var input_group_row_list = [];
		  input_group_row_list = [];
          var input_string = "";
          var row_values = {};
          row_counter += 1;

		  //Go through each input in the row
		  $( this ).find("input").each(function( index ) {
			  var my_key = $( this ).attr('data-sub-field-name');
			  var my_value = $( this ).val();


              if ($( this ).attr('type') == "file") {
			      if (my_value != "") {

			          $.each($(this).prop('files'), function(index, file) {
						  //Post the file directly since we can't strinify it
						  var post_name = html_name + "_" + row_counter + "_" + my_key;
						  form_values[post_name] = file;

			              row_values[my_key] = post_name;
					  });

		          }
		      } else {
			      if (my_value != "") {
			          row_values[my_key] = my_value;
		          }
		      }
		  });

		  //Go through each selection in the row
		  $( this ).find("select").each(function( index ) {
			  var my_key = $( this ).attr('data-sub-field-name');
			  var my_value = $( this ).val();

			  if (my_value != "") {
			      row_values[my_key] = my_value;
		      }
		  });

          if(! jQuery.isEmptyObject(row_values) ) {
              input_group_list.push(row_values);
	      }

	  });

	  if (input_group_list.length > 0) {
        form_values[html_name] = JSON.stringify(input_group_list);
      }

    });

    //Have to get the files manually
    _.each(my_form.find('input[type=file]'), function(input) {
      $.each($(input).prop('files'), function(index, file) {
          form_values[input.name] = file;
        });
    });

    form_values['is_ajax_post'] = "Yes";

    // Post form and handle result
    ajax.post(my_form.attr('action'), form_values).then(function(result_data) {

      try {
        result_data = $.parseJSON(result_data);
      } catch(err) {
        alert("An error has occured during the submittion of your form data\n" + result_data);
      }


      if (result_data.status == "error") {
        for (var i = 0; i < result_data.errors.length; i++) {
		  //Find the field and make it displays as an error
          var input = my_form.find("input[name='" + result_data.errors[i].html_name + "']");
          var parent_div = input.parent("div");

          //Remove any existing help block
          parent_div.find(".help-block").remove();

          //Insert help block
          input.after("<span class=\"help-block\">" + result_data.errors[i].error_messsage + "</span>");
          parent_div.addClass("has-error");
        }
      } else if (result_data.status == "success") {
	      window.location = result_data.redirect_url;
      }

    });

  });

});

});