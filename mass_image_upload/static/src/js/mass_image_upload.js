odoo.define('mass_image_upload.mass_image_upload', function (require) {
"use strict";

    var core = require('web.core');
    var base = require('web_editor.base');
    var Model = require('web.Model');
    var session = require('web.session');

    var _t = core._t;

    $(document).ready(function () {




  function handleFileSelect(evt) {
    var files = evt.target.files; // FileList object

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

          mapField = document.getElementById('mapField').value;



    	  session.rpc('/mass/image/upload/file', {'base64string': base64string, 'fileName': theFile.name,'mapField': mapField}).then(function(result) {
			  if (result.status == "success") {
				  $('#massimageuploadsuccess').append(result.message + "\n");
			  } else if(result.status == "error") {
				  $('#massimageuploaderror').append(result.message + "\n");
		      }
          });


        };


      })(f);

      // Read in the image file as a data URL.
      reader.readAsDataURL(f);
    }
  }

  document.getElementById('mass_image_upload_input').addEventListener('change', handleFileSelect, false);






    });

});