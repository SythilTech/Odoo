v1.4.6
======
* Character set in DSN template

v1.4.5
======
* Date and integer validation

v1.4.4
======
* Many2one auto remapping and validation taking into account remapping

v1.4.3
======
* Set limit on import per batch so large dataset can be imported 100 records at a time rather then clogging the system for hours
* Import files now occurs the same time as importing other data

v1.4.2
======
* Boolean validation and auto remapping

v1.4.1
======
* Auto remap for selection fields
* Take selection remap into consideration for valid check

v1.4
====
* Change date format during import

v1.3
====
* Fix issue with no _origin.id by removing onchange validation
* Fix issue with remap values being added twice

v1.2.2
======
* Download files by URL

v1.2.1
======
* Many2one validation

v1.2
====
* Validate fields as you map them
* Bug fix 0 blank distinct values

v1.1
====
* Simplify creation of connetion strings
* Add primative table validation
* View distinct values of a column (designed to assist importing data into selection fields)

v1.0
====
* Initial Release