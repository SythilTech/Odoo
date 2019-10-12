v2.0.2
======
* Fix access rights for non support staff employees

v2.0.1
======
* Fix permission issue

v2.0.0
======
* Remove dependacy on crm module

v1.6.1
======
* Fix upgrade issue for people pre version 1.6.0 related to default approval

v1.6.0
======
* Add approval field
* Add request approval button
* Add approve and disapprove links to email
* Change unattended tickets filter to any state except closed or staff replied

v1.5.14
=======
* Remove read only from state to allow custom states management (dont bypass the automation...)
* Kanban group by state
* Kanban render html
* Custom fields add yes / no type

v1.5.13
=======
* Support ticket kanban view

v1.5.12
=======
* Fix issue with extra fields not disappearing after category change
* Change default staff repy to user and remove support

v1.5.11
=======
* Fix missing field and department permissions

v1.5.10
=======
* Remove automatic mail followers of tickets

v1.5.9
======
* Fix mismapping of support ticket custom fields

v1.5.8
======
* New contacts are explicted a person (change to support partner_auto_parent_company)

v1.5.7
======
* New setting to auto create contacts

v1.5.6
======
* Custom fields permission fix
* Reduce font size of support headings

v1.5.5
======
* Additional fields depending on selected sub category
* Hide blank one2many fields to keep support ticket view small

v1.5.4
======
* Fix blank attachments issue
* Fix public no permision to create attachment issue
* Allow download of attachments from backend

v1.5.3
======
* Order help groups
* Order help pages
* Publish / unpublish help groups
* Publish / unpublish help pages
* Force style of help groups and helps pages so design is consistant across different themes
* Limit access to help groups to particular groups

v1.5.2
======
* Fix "Support Ticket Reply Wrapper (support@)" email from

v1.5.1
======
* Few extra report stats

v1.5.0
======
* Departments which are a grouping of support users with assigned managers for reporting

v1.4.24
=======
* Auto send survey setting

v1.4.23
=======
* Read only rating and comment
* Readd portal key for logged in users since it's used by survey

v1.4.22
=======
* State assignable email

v1.4.21
=======
* Sub category sequence

v1.4.20
=======
* Help group access only to certain contacts

v1.4.19
=======
* Create user account setting

v1.4.18
=======
* Help group access groups

v1.4.17
=======
* Category sequence

v1.4.16
=======
* Closed by user field

v1.4.15
=======
* Mail template field

v1.4.14
=======
* Hidden create user field

v1.4.13
=======
* Add multiple attachments to support tickets + settings to limit quantity and filesize

v1.4.12
=======
* Close wizard using python window action

v1.4.11
=======
* Remove new ticket in category email from chatter

v1.4.10
=======
* Logged in users that submit tickets via the website no longer get website portal access (security precaution since website portal doesn't require any login)

v1.4.9
======
* Remove message button in chatter since it bypasses reply code

v1.4.8
======
* support email template fix
* conversation history from is based on person_name or email not create_uid

v1.4.7
======
* Fix bug with multi ticket access allow only allowing single extra access

v1.4.6
======
* Restrict Customer Support menu to only the "Sales / Manager" and Sales / Users: All Docuemnts"

v1.4.5
======
* Use comapany email in all cases

v1.4.4
======
* Filter out system emails and make it easier to create new email templates

v1.4.3
======
* Send email when user is assigned

v1.4.2
======
* Restrict support ticket menu to employee only since sometimes portal could gain access?

v1.4.1
======
* Compatablity with web_list_autorefresh module

v1.4
====
* Setting to change staff reply email template

v1.3.9
======
* Prevent tickets with no partner displaying in website portal

v1.3.8
======
* Render HTML ticket description in website portal

v1.3.7
======
* Default category for email ticket setting
* Public website portal access to tickets created via email
* Support ticket manager access field
* Add group by category and user

v1.3.6
======
* Close email template setting
* Change categories, priorities and state to not update so changes are preserved across versions
* Ticket survey now uses images to represent rating

v1.3.5
======
* Fix email sanitisation issue

v1.3.4
======
* close ticket permission fix

v1.3.3
======
* close ticket comment

v1.3.2
======
* Sub categories permission fix

v1.3.1
======
* Sub categories on website form

v1.3
====
* Sub categories and support survey

v1.2.10
=======
* Blank category staff reply fix

v1.2.9
======
* Manual html sanitise

v1.2.8
======
* Remove readonly restrictions

v1.2.7
======
* Remove required and create restrictions

v1.2.6
======
* Fix support ticket by email

v1.2.5
======
* Added help page menu and help page count fix

v1.2.4
======
* translate help pages name fix

v1.2.3
======
* translate help pages fix

v1.2.2
======
* category email not replacing placeholders

v1.2.1
======
* non employee user permission fix

v1.2
====
* Transfer revamp changes from v9

v1.1
====
* Transfer ticket number and priority coloring from v9

v1.0.1
======
* Version 10 fixes

v1.0
====
* Version 10 upgrade