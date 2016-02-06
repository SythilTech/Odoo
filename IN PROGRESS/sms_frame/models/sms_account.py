from openerp import models, fields, api

class SmsAccount(models.Model):

    _name = "sms.account"
    
    name = fields.Char(string='Account Name', required=True)
    account_gateway = fields.Many2one('sms.gateways', string="Account Gateway", required=True)

    @api.model
    def check_all_messages(self):                
        my_accounts = self.env['sms.account'].search([])
        for sms_account in my_accounts:            
            self.env[sms_account.account_gateway.gateway_model_name].check_messages(sms_account.id)