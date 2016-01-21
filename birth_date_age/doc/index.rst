Inherited Views
===============
res.partner.form (base.view_partner_form)
-----------------------------------------
Adds ``birth_date`` and ``age`` fields just below ``website`` field.

Models / Fields
===============
res.partner(inherit)
--------------------
**DOB (birth_date)**: Stores the partner date of birth

**Age (age)**: Partner age updated every 24 hours by dba_update

Inserted Records
================
ir.cron
-------
**Partner Age Update (dba_update)**: Updates the age of all partners