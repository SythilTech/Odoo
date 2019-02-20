# -*- coding: utf-8 -*-
from openerp import api, fields, models

class MailActivityTwilioVoip(models.Model):

    _inherit = "mail.activity"

    activity_type_id_ref = fields.Char(string="Activity Type External Reference", compute="_compute_activity_type_id_ref")

    @api.depends('activity_type_id_ref')
    def _compute_activity_type_id_ref(self):
        if self.activity_type_id:
            external_id = self.env['ir.model.data'].sudo().search([('model', '=', 'mail.activity.type'), ('res_id', '=', self.activity_type_id.id)])
            if external_id:
                self.activity_type_id_ref = external_id.complete_name

    @api.multi
    def twilio_mobile_action(self):
        self.ensure_one()

        #Call the mobile action of whatever record the activity is assigned to (this will fail if it is not crm.lead of res.partner)
        assigned_record = self.env[self.res_model].browse(self.res_id)
        return assigned_record.twilio_mobile_action()