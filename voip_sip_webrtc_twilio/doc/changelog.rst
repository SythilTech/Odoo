v1.0.24
=======
* Redirect to record after making call comment

v1.0.23
=======
* Add 'Make Twilio Call' button to activity screen to optimise workflow

v1.0.22
=======
* Call log report now has total cost / total duration
* Invoices created by the Create Invoice button will generate a unique pdf more tailored to calls (e.g. no quantity column)

v1.0.21
=======
* Fix Call History report and add ability to skip report (can be time consuming)

v1.0.20
=======
* Fix JWT renewal for incoming calls

v1.0.19
=======
* Feature to assign a number to a user to speed up calling

v1.0.18
=======
* Display user friendly error if call fails for any reason e.g. no media access

v1.0.17
=======
* Smart button on Twilio account screen that shows calls for that account

v1.0.16
=======
* Code out the need to have the Twilio Python library installed for capabilty token generation

v1.0.15
=======
* Fix call history import

v1.0.14
=======
* Fix cability token url using http in https systems

v1.0.13
=======
* Fix mySound undefined bug on outgoing calls

v1.0.12
=======
* Automatically generate Twilio client name

v1.0.11
=======
* Ability to call leads

v1.0.10
=======
* Can now write a post call comment, you can also listen to call recording using a link inside the chatter
* Call recordings are no longer downloaded, instead only the url is keep (prevents post call hang due to waiting for download + increased privacy / security not having a copy inside Odoo)

v1.0.9
======
* Update Import call history to also import call recordings
* Calls are now added to the Odoo call log with their recordings

v1.0.8
======
* Bug fix to also record outgoing SIP calls not just the Twilio javascript client ones.

v1.0.7
======
* Twilio capability token generation (easy setup)

v1.0.6
======
* Fix incorrect voice URL

v1.0.5
======
* Answer calls from within your browser

v1.0.4
======
* Merge with twilio bill and introduce manual call functionality

v1.0.0
======
* Port to version 11