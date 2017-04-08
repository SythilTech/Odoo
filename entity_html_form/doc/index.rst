Menus
=====
HTML Embed Forms
----------------
Child of "Settings" menu, parent menu of all other eHTML menus

Create Forms
------------
Child of "HTML Embed Forms" menu, place to create HTML forms

Inserted Form Data
------------------
Child of "HTML Embed Forms" menu, history of all form submissions

Models / Fields
===============
ehtml.formgen(An individual Form)
---------------------------------
Permissions
^^^^^^^^^^^
**Administration / Settings (base.group_system)**: Read, Write, Create and Delete

Fields
^^^^^^
**Form Name (name)**: Human meaningful name for the form

**Model (model_id)**: The model which the form is based around

**HTML Fields (fields_ids)**: The list of Odoo fields in the HTML form

**Embed Code (output_html)**: The output HTML designed to be copied and pasted into an external site

**Required Fields (required_fields)**: Human readable list of fields that are required for that model

**Default Values (defaults_values)**: List of fields and a corresponding default value which is set when the record is created

**Return URL (return_url)**: After the form is submitted the user is redirected to this URL

**Form Type (form_type)**: The format of the outputted HTML, Odoo or native

ehtml.fieldentry(A field in the form)
-------------------------------------
Permissions
^^^^^^^^^^^
**Administration / Settings (base.group_system)**: Read, Write, Create and Delete

Fields
^^^^^^
**Sequence (sequence)**: Drag and drop field order

**HTML Form (html_id)**: ID pointing back to the HTML form

**Model (model_id)**: The model ID of the field hidden from user sight

**Related Model (model)**: The model name of the field hidden from user sight

**Form Field (field_id)**: The Odoo field this form field inserts data into

**Field Label (field_label)**: Human readable label for the field on the website

**HTML Field Name (html_name)**: The HTML name of the field handy for autocomplete e.g auto fill email/mobile

**HTML Field Type (html_field_type)**: The type of HTML input to use for this type of field

ehtml.fielddefault (Stores the default values for each form)
------------------------------------------------------------
Permissions
^^^^^^^^^^^
**Administration / Settings (base.group_system)**: Read, Write, Create and Delete

Fields
^^^^^^
**HTML Form (html_id)**: ID pointing back to the HTML form

**Model (model_id)**: Model ID, hidden from user

**Model Name (model)**: Model Name, hidden from user

**Form Fields (field_id)**: The Odoo field your settings a default value for

**Default Value (default_value)**: The value that is set for this Odoo field when the record is inserted

ehtml.history (Stores all inserted records)
-------------------------------------------
Permissions
^^^^^^^^^^^
**Administration / Settings (base.group_system)**: Read

Fields
^^^^^^
**HTML Form (html_id)**: ID pointing back to the HTML form

**Reference URL (ref_url)**: The URL this form waas submitted from

**Record ID (record_id)**: The ID of the inserted record

**Form Name (form_name)**: No Idea...

**HTML Fields (insert_data)**: List of data that was inserted with this submission

ehtml.fieldinsert (History of the field data that was inserted)
---------------------------------------------------------------
Permissions
^^^^^^^^^^^
**Administration / Settings (base.group_system)**: Read

Fields
^^^^^^
**HTML Form (html_id)**: ID pointing back to the HTML form history

**Field (field_id)**: The field that data was inserted into

**Insert Value (insert_value)**: The value inserted


Security
========
Administration / Settings (base.group_system)
---------------------------------------------
**ehtml.formgen**: Read, Write, Create and Delete

**ehtml.fieldentry**: Read, Write, Create and Delete

**ehtml.fielddefault**: Read, Write, Create and Delete

**ehtml.history**: Read

**ehtml.fieldinsert**:  Read