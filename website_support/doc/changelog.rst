v1.9.13
=======
* Help page Sanitize fix 

v1.9.12
=======
* Translate help pages name fix 

v1.9.11
=======
* Translate help pages fix

v1.9.10
=======
* Category email is now user language

v1.9.9
======
* Automatically find partner when someone sends a ticket in via email

v1.9.8
======
* Attempt to remove email client wrapping

v1.9.7
======
* Category email not replacing palceholders issue

v1.9.6
======
* non employee user permission fix

v1.9.5
======
* Fix permission issue with public users submitting reply via website

v1.9.4
======
* Move ticket setup code to create method so new tickets received via mail send out auto reply and category users

v1.9.3
======
* New ticket and new ticket in cateogry email template can now be modified

v1.9.2
======
* Change ticket seq number in company form view

v1.9.1
======
* Prevent manual creation of tickets since the setup is done via the controller

v1.9
====
* Fake ticket numbers to hide company size
* Color code priorities

v1.8
====
* Create support ticket directly from new email

v1.7.14
=======
* Anti spam for support ticket form
* Prevent upload of exe's

v1.7.13
=======
* fix email support ticket link returning false(again)...

v1.7.12
=======
* Fix email support ticket link returning false
* Send initial email after ticket is submitted


v1.7.11
=======
* Portal access for publicly sent tickets

v1.7.10
=======
* Strip reply footer when someone replies via email
* Remove communication history from form view
* Add portal_access_key field in preparation for letting public users view thier ticket inline

v1.7.9
======
* Allow changing of partner
* Swap description for subject in support ticket tree view 

v1.7.8
======
* Fix missing permission

v1.7.7
======
* New ticket count on partner view

v1.7.6
======
* Automatic partner detection

v1.7.5
======
* Fix bug when Open state name was changed
* Fix bug where state would be stuck in Customer replied

v1.7
====
* Ticket priority

v1.6
====
* Full email integration

v1.4.8
======
* Translatable state and categories

v1.4.7
======
* Add blank header for addon module

v1.4.6
======
* Add graph view for basic reporting

v1.4.5
======
* State and category change now use the native mail track_visibility
* User support ticket comments now add to the communication history

v1.4.4
======
* Display menu number for unanswered tickets

v1.4.3
======
* Average rating becomes 0 if thier is no feedback

v1.4.2
======
* Default support ticket filter

v1.4.1
======
* Category email now uses  user.partner_id.email rather then user.login
* Category email now users 'Dear user.partner_id.name' rather incorrectly greeting the user with the support ticket email

v1.4
====
* Default permissions, help page search and notification email link improvements

v1.3.1
======
* Changes to category and state add to the message log

v1.3
====
* Added message log

v1.2
====
* Public users can submit feedback on each help page

v1.1
====
* Added file attachment input to submit tick form

v1.0
====
* Initial release