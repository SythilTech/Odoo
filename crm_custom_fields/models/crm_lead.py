# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID

class CRMLeadConert(models.Model):

    _inherit = "crm.lead"
    
    @api.multi
    def _lead_create_contact(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        email_split = tools.email_split(self.email_from)
        values = {
            'name': name,
            'user_id': self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_split[0] if email_split else False,
            'fax': self.fax,
            'title': self.title.id,
            'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'is_company': is_company,
            'type': 'contact'
        }

        for convert_field in self.env['sale.config.settings.convert'].search([]):
            values[convert_field.partner_field_id.name] = self[convert_field.lead_field_id.name]
        
        return self.env['res.partner'].create(values)

