odoo.define('mass_image_upload.mass_image_upload', function (require) {
"use strict";

    var core = require('web.core');
    var base = require('web_editor.base');
    var Model = require('web.Model');
    var session = require('web.session');

    var _t = core._t;

    $(document).ready(function () {

        $("#mass_image_upload_button").click(function() {

            var file_input = document.getElementById('mass_image_upload_input');
            var files = file_input.files; // FileList object
            var complete_count = 0;

            // Loop through the FileList and upload each one.
            for (var i = 0, f; f = files[i]; i++) {


                // Only process image files.
                if (!f.type.match('image.*')) {
                  continue;
                }

                var reader = new FileReader();

                // Closure to capture the file information.
                reader.onload = (function(theFile) {
                  return function(e) {

                    var base64string = e.target.result.split(',')[1];
                    var mapField = document.getElementById('mapField').value;
                    var message = ""
                    var status = "";
setTimeout(function() {
                    $.ajax({
                      url: "/mass/image/upload/file",
                      type: 'POST',
                      dataType: 'json',
                      contentType: 'application/json',
                      data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'base64string': base64string,'fileName': theFile.name,'mapField': mapField} }),
                      async: false,
                      success: function (result) {
		          		console.log(complete_count + ". " + result.result.status + "," + result.result.message);

		          		status = result.result.status;
		          		message = result.result.message;

                    	complete_count += 1;

		            	if (status == "success") {
		            	    $('#massimageuploadsuccess').append(complete_count + ". " + message + "\n");
		            	} else if(status == "error") {
		            	    $('#massimageuploaderror').append(complete_count + ". " + message + "\n");
		            	}

		            	$('#complete_count').html(complete_count);


                      },
                    });

}, 0);



                  };


                })(f);

                // Read in the image file as a data URL.
                reader.readAsDataURL(f);

		    }


         });

     });


});