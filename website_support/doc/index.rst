Inherited Views
===============
res.partner.form (base.view_partner_form)
-----------------------------------------
Adds "Support Tickets" button in the top right button box.

Web Controllers
===============
/support/help
-------------
Public, lists help groups and their help pages.

/support/ticket/submit
----------------------
Public, Page where public / registered users can submit a support ticket.

/support/ticket/process
-----------------------
Public, insert support ticket into database, send email to all follows of the tickets support category and redirect user to thank you page.

/support/ticket/thanks
----------------------
Public, thanks the users for submitting the ticket.

/support/ticket/view
--------------------
User, views a list of support tickets submitted by the logged in user.

/support/ticket/view/<ticket>
-----------------------------
User, views an individual ticket with the id <ticket>, shows error if the ticket is not owned by the logged in user.

/support/ticket/comment
-----------------------
User, Inserts support ticket comment into database and redirects user back to /support/ticket/view/<ticket> page.

/support/help/auto-complete
---------------------------
Public, broken but it's meant to allow people to search for help pages.

Menus
=====
Customer Support
----------------
Child of "Sales" menu, parent menu of all sales team related support ticket menus

Support Tickets(staff)
----------------------
Child of "Customer Support" menu, lets the sales team view all support tickets

Support Tickets(admins)
-----------------------
Child of "Sales / Configuration" menu, lets admin config all settings related to the support ticket system

Help Pages
----------
Child of "Support Tickets", lets you create help pages which help reduce the amount of support tickets sent by explaining most commonly asked questions

States
------
Child of "Support Tickets", lets you configure the states a support ticket can be in

Inserted Records
================
website.menu
----------------
**Support (website_support_ticket)**: Adds "Support" to your website main menu.

website.support.ticket.categories
---------------------------------
**Technical Support (website_support_tech_support)**: "Tech Support" ticket category.

**Billing Issues (website_support_billing_issues)**: "Billing Issues" ticket category.

website.support.ticket.states
-----------------------------
**Open (website_ticket_state_open)**: A ticket that is new/open

**Staff Replied (website_ticket_state_staff_replied)**: A ticket staff have replied to

**Customer Replied (website_ticket_state_customer_replied)**: A ticket the customer has replied to

**Customer Closed (website_ticket_state_customer_closed)**: The customer has deemed the issue fixed and has closed the ticket

**Staff Closed (website_ticket_state_staff_closed)**: The staff consider the issue fixed or have not got a reply in a long time and have closed the ticket

Models / Fields
===============
res.partner (Inherited)
-----------------------
Fields
^^^^^^
**Tickets (support_ticket_ids)**: Support ticket list in the form of a button

**Ticket Count (support_ticket_count)**: The amount of support tickets this customer has

website.support.help.groups (Support help articles are grouped together under a common title)
---------------------------------------------------------------------------------------------
Fields
^^^^^^
**Help Group (Help Group)**: Name of the help group as displayed on the website

**Pages (page_ids)**: List of help page articles that are part of this group

**"Number of Pages (page_count)**: number of help page articles in this group

website.support.help.page (An individual help article)
------------------------------------------------------
Fields
^^^^^^
**Page Name (name)**: Name of the help page

**Page URL (url)**: Auto generated url of the help page

**Group (group_id)**: The help group this page belongs too

website.support.ticket (A support ticket)
-----------------------------------------
Fields
^^^^^^
**Partner (partner_id)**: The partner this ticket belongs to if any

**Person Name (person_name)**: The name of the person that submitted the ticket

**Email (email)**: The name of the person that submitted the ticket

**Category (category)**: The category of the support ticket

**Subject (subject)**: The subject of the support ticket, remains the same throughout the life cycle of the ticket

**Description (description)**: The initial content of the support ticket when it was first submitted

**State (state)**: The current state of the support ticket, starts as open ends with closed

**Conversation History (conversation_history)**: History of the conversation between various staff and the customer

website.support.ticket.message (A message in a support ticket conversation)
---------------------------------------------------------------------------
Fields
^^^^^^
**Ticket ID (ticket_id)**: The ticket this message belongs too

**Content (content)**: the content of the message

website.support.ticket.categories (Categories a support ticket can be)
----------------------------------------------------------------------
Fields
^^^^^^
**Category Name (name)**: Name of the category as seen in the support ticket submit webpage


website.support.ticket.states (The states a ticket can be in, starts as open, goes back and forth between customer replied and staff replied and finally closes when the issue has been resolved)
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Fields
^^^^^^
**State Name (name)**: Name of the state as seen by staff

Security
========
No Group ()
-----------
**website.support.ticket**: Read, Write and Create

**website.support.ticket.states**: Read

**website.support.ticket.message**: Read and Create