v.1.8.2
=======
* Dedicated settings view for textboxes(others fields types will come later)

v.1.8.1
=======
* Fail safe form validation for javascript disabled and external forms

v.1.8
=====
* Tidy up genersated html
* Fix issue preventing adding new html fields
* Misc changes to adapt to new ajax form posting

v.1.7.2
=======
* field labels are always bold, required will be reworked

v.1.7.1
=======
* Fail safe required validation

v.1.7
=====
* Datetime generation

v.1.6.10
========
* CSS clean to get the drag and drop functing like it should
* Disabled field size changing, to be replaced with grid system module

v.1.6.9
=======
* csrf as causing snipet issues, it will be replaced with an allow external access button with domain whitelist

v.1.6.8
=======
* Set default permissions to shut log up

v.1.6.7
=======
* Increase security

v.1.6.6
=======
* Add date picker field

v.1.6.5
=======
* Change required to required="required" so Odoo is happy

v.1.6.4
=======
* Let people configure captcha from front end
* Few CSS fixes so Captcha is aligned correctly
* Change it so field width only applies to form fields

v.1.6.3
=======
* Remove display_name from field list since it creates major confusion

v.1.6.2
=======
* 2nd Captcha fix
* Fix form field margin issue 
* Added role to forms
* Added character limit validation

v1.6.1
======
* Fixed issue with recaptcha breaking after page changes (resets recaptcha after every save)

v1.6
====
* Added field format validation(email)

v1.5.2
====
* Fixed issue where recaptcha was loaded twice
* Fixed issue where (non admin)web designers couldn't use snippets

v1.5.1
====
* Fixed issue relating to captcha not working for public user
* Fixed issue with Captcha not added alongside an existing form

v1.5
====
* Added checkbox(boolean) field

v1.4
====
* Added 2 fields, dropbox(many2one) and radio button group(selection)

v1.3
====
* Can now create new forms directly from the website builder
* Can now resize fields 1/2, 1/3 and 1/4
* Field type limit for each type of field e.g. Can no longer select Many2one field for textboxes.

v1.0
====
* Initial realease 