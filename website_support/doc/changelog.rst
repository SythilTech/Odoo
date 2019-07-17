v1.6.8
======
* Fix comment attachments in portal reply

v1.6.7
======
* Fix help pages 404

v1.6.6
======
* Ability to set a default body and cc depending on ticket contact, which auto fills the ticket reply wizard

v1.6.5
======
* Fixed bug with department manager not being able to view individual tickets

v1.6.4
======
* Add create support ticket button to form view

v1.6.3
======
* Prevent direct help page access

v1.6.2
======
* Clears sub category on category change to prevent saving with sub category of old parent

v1.6.1
======
* Change close template to allow blank closing comment

v1.6.0
======
* Add merge ticket button
* Add close lock feature to prevent reopening tickets (auto lock upon ticket merge)

v1.5.16
=======
* Add many2one type to custom fields

v1.5.15
=======
* Add setting to auto create contact

v1.5.14
=======
* Add ability to add attachments on staff reply and staff ticket close

v1.5.13
=======
* Adjust permissions so employees can view contacts without access to support ticket data.

v1.5.12
=======
* Add ability for clients to add attachments in there replies from the website interface

v1.5.11
=======
* Suggest help pages that are similiar to ticket subject (reduces tickets submitted that already have a help article)

v1.5.10
=======
* Changes courtesy of lucode (https://github.com/SythilTech/Odoo/pull/60)
* Adding some UX related logic to Support Ticket view.
* Updating french / german language
* Adding new client form view. Old view is still default one.
* New client form view. state readonly in view.

v1.4.9
======
* Change close email template to support html and remove from form view as it is displayed in chatter anyway.

v1.4.8
======
* Fix spelling mistake sanatize=False to sanitize=False, which should allow things like youtube videos and other stuff to be placed in help pages like it was designed to do...
* Add help page attachments

v1.4.7
======
* Fix upgrade issue for people before version 1.1.0 related to approval

v1.4.6
======
* Fix permission issues with support clients assigned as department managers not being able to view website reporting interface

v1.4.5
======
* Fix approval mail permissions

v1.4.4
======
* Close ticket email templates
* Fix Fix help page search
* Fix double close comment email bug

v1.4.3
======
* Fix permission issue with survey and change requests being inaccessible for public users

v1.4.2
======
* Fix ticket submit issue with public users with existing emails submitting tickets (introduced in v1.4.0)

v1.4.1
======
* Fix issue with survey link appearing as _survey_url_ in chatter

v1.4.0
======
* SLA overhaul to support multiple conditions e.g. Priority = Urgent AND Category = Technical Support
* Fix Issue with Support Managers access being lost on module update (will apply to future versions)
* Ability to add image to help groups (optional)

v1.3.12
=======
* Department manager access to department contact tickets fix
* Automatically add category follower to ticket followers

v1.3.11
=======
* Ability to assign a customer to a dedicated support staff member

v1.3.10
=======
* Help page unpublish / republish

v1.3.9
======
* Fix signed in users not being able to access help groups / pages

v1.3.8
======
* Fix help group page using old field

v1.3.7
======
* Add customer close button
* Limit help pages to 5 per help group with a more link
* Administrator now defaults to Support Manager to help reduce install confusion

v1.3.6
======
* User accounts created through the create account link are now added to the portal group instead of the public group to resolve login issues

v1.3.5
======
* Fix business hours field missing resource module dependacy

v1.3.4
======
* Ability to limit which user groups can select a category

v1.3.3
======
* Add close date to customer website portal

v1.3.2
======
* Assigned user filter for internal users (employees) only

v1.3.1
======
* Remove dependency on CRM module

v1.3.0
======
* (BACK COMPATABLITY BREAK) Remove old Sales Manager permissions
* Group and permission overhaul (Support Client, Support Staff, Support Manager)
* Update documentation to reflect menu changes and permission overhaul

v1.2.14
=======
* Adding sequence for ticket number, deleting ticket number display
* Migrate fake ticket number system to sequence system
* Spanish tranlation
* Timezone in website view
* Various view improvements

v1.2.13
=======
* Optional priority field on website

v1.2.12
=======
* Website filter state for tickets
* Hide SLA resume and pause buttons if no SLA is assigned to the ticket
* Choose which states get classified as unattended

v1.2.11
=======
* Unlinked page to list help pages by support group

v1.2.10
=======
* Fix SLA business hours timer and add support for holidays via the hr_public_holidays module

v1.2.9
======
* Permission for SLA Alerts

v1.2.8
======
* SLA alert emails

v1.2.7
======
* reCAPTCHA implementation since the honey pot is not bullet proof

v1.2.6
======
* SLA tickets now have a timer that counts down, you can select between always count and business hours only + plus/resume timer

v1.2.5
======
* Ability to assign SLA to contact and ultimately to their tickets

v1.2.4
======
* Information only SLA

v1.2.3
======
* Planned date now in default wrapper email template, formatted and localised
* Default wrapper email template now uses fake/display ticket_number not id

v1.2.2
======
* Portal access key is generated when ticket is manually created or through email / website

v1.2.1
======
* Permission fix for approval system

v1.2.0
======
* Ability to tag support tickets

v1.1.1
======
* Support ticket now defaultly searches by subject rather then partner...

v1.1.0
======
* Port approval system over from version 10
* Add approvals to portal
* Email notifacation on approval / rejection
* Default approval compose email is now a email tempalte rather then hard coded.

v1.0.12
=======
* Changing subcategory now automatically adds th extra fields

v1.0.11
=======
* Extra field type and label is required

v1.0.10
=======
* Show extra fields incase someone wants to manuall add the data
* Add new channel field which tracks the source of the ticket (website / email)

v1.0.9
======
* Remove kanban "+" and create since it isn't really compatable

v1.0.8
======
* Fix subcategory change not disappearing
* States no longer readonly
* Move Kanban view over from Odoo 10

v1.0.7
======
* Fix subcategories

v1.0.6
======
* Fix multiple ticket delete issue

v1.0.5
======
* Change default email wrapper to user

v1.0.4
======
* Remove obsolete support@ reply wrapper

v1.0.3
======
* Fix website ticket attachment issue

v1.0.2
======
* Fix settings screen and move menu

v1.0.1
======
* Forward fix custom field mismatch

v1.0
====
* Port to version 11