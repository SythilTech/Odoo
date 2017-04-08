Inherited Views
===============
marketing.campaign.activity.form (marketing_campaign.view_marketing_campaign_activity_form)
-------------------------------------------------------------------------------------------
Adds ``sms_template_id`` field to view just below ``type`` field, which is only visible when ``type`` is set to ``sms`` 

Models / Fields
===============
marketing.campaign.activity (Inherited)
---------------------------------------
Fields
^^^^^^
**Type (type)**: Inherits, adds ``sms`` to selection

**SMS Template (sms_template_id)**: The SMS template used in the activity