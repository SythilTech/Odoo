# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class PaymentMembership(models.Model):

    _name = "payment.membership"

    name = fields.Char(string="Name", required=True)
    subscription_id = fields.Many2one('payment.subscription', string="Subscription")
    redirect_url = fields.Char(string="Redirect URL", default="/membership/signup/thank-you")
    group_ids = fields.Many2many('res.groups', string="New User Groups", help="Determines what the user can access e.g. slide channels / support help groups")
    extra_field_ids = fields.One2many('payment.membership.field', 'payment_membership_id', string="Extra Fields", help="More fields will appear on the website signup form")
    member_ids = fields.One2many('res.partner', 'payment_membership_id', string="Members")

    @api.multi
    def view_singup_form(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_url',
            'name': "Membership Signup Form",
            'target': 'self',
            'url': "/membership/signup/" + slug(self)
        }
        
class PaymentMembershipField(models.Model):

    _name = "payment.membership.field"

    payment_membership_id = fields.Many2one('payment.membership', string="Payment Membership")
    field_id = fields.Many2one('ir.model.fields', string="Field", domain="[('model_id.model','=','res.partner')]", required=True)
    name = fields.Char(string="Name")
    field_type = fields.Selection([('textbox','Textbox')], string="Field Type", default="textbox", required=True)
    field_label = fields.Char(string="Field Label", required=True)

    @api.onchange('field_id')
    def _onchange_field_id(self):
        if self.field_id:
            self.field_label = self.field_id.field_description
            self.name = self.field_id.name