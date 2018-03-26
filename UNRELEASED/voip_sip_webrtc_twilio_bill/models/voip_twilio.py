# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import json
import requests
from datetime import datetime, timedelta
import re
from odoo.exceptions import UserError
from dateutil import parser

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import api, fields, models

class VoipTwilio(models.Model):

    _name = "voip.twilio"
    _description = "Twilio Account"

    name = fields.Char(string="Name")
    twilio_account_sid = fields.Char(string="Account SID")
    twilio_auth_token = fields.Char(string="Auth Token")
    twilio_last_check_date = fields.Datetime(string="Last Check Date")
    resell_account = fields.Boolean(string="Resell Account")
    margin = fields.Float(string="Margin", default="1.1", help="Multiply the call price by this figure 0.7 * 1.1 = 0.77")
    partner_id = fields.Many2one('res.partner', string="Customer")

    @api.multi
    def create_invoice(self):
        self.ensure_one()

        if self.partner_id.id == False:
            raise UserError("Please select a contact before creating the invoice")
            return False

        return {
            'name': 'Twilio Create Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'voip.twilio.invoice',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_twilio_account_id': self.id, 'default_margin': self.margin, 'default_end_date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT), 'default_start_date': (datetime.now() - timedelta(days=30)).strftime(DEFAULT_SERVER_DATE_FORMAT) }
        }

    def fetch_call_history(self):

        payload = {}
        if self.twilio_last_check_date:
            my_time = datetime.strptime(self.twilio_last_check_date,'%Y-%m-%d %H:%M:%S')
            response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/Calls.json?StartTime%3E=" + my_time.strftime('%Y-%m-%d'), auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
        else:
            response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/Calls.json", auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))

        json_call_list = json.loads(response_string.text)

        _logger.error(response_string.text)

        if 'calls' not in json_call_list:
            raise UserError(response_string.text)

        for call in json_call_list['calls']:

            #Don't reimport the same record
            if self.env['voip.call'].search([('twilio_sid','=',call['sid'])]):
               continue

            from_partner = False
            from_address = call['from']
            to_address = call['to']
            to_address = to_address.replace("sip:","")
            to_partner = False
            create_dict = {}

            create_dict['twilio_account_id'] = self.id

            if 'price' in call:
                if call['price']:
                    if float(call['price']) > 0.0:
                        create_dict['currency_id'] = self.env['res.currency'].search([('name','=', call['price_unit'])])[0].id
                        create_dict['price'] = -1.0 * float(call['price'])

            #Format the from address and find the from partner
            if "+" in from_address:
                #Mobiles should conform to E.164
                from_partner = self.env['res.partner'].search([('mobile','=',from_address)])
            else:
                #SIP addresses are messy and incomplete
                from_address = from_address.replace(";region=gll","")
                from_address = from_address.replace(":5060","")
                from_address = from_address.replace("sip:","")

                if "@" not in from_address:
                    _logger.error(to_address)
                    #Get the full aor based on the domain of the to address
                    domain = re.findall(r'@(.*?)', to_address)[0].replace(":5060","")
                    from_address = from_address + "@" + domain

                from_partner = self.env['res.partner'].search([('sip_address','=', from_address)])

            if from_partner:
                #Use the first found partner
                create_dict['from_partner_id'] = from_partner[0].id
            create_dict['from_address'] = from_address

            #Format the to address and find the to partner
            if "+" in to_address:
                #Mobiles should conform to E.164
                to_partner = self.env['res.partner'].search([('mobile','=',to_address)])
            else:
                #SIP addresses are messy and incomplete
                to_address = to_address.replace(";region=gll","")
                to_address = to_address.replace(":5060","")
                to_address = to_address.replace("sip:","")

                if "@" not in to_address:
                    #Get the full aor based on the domain of the from address
                    domain = re.findall(r'@(.*?);', from_address)[0].replace(":5060","")
                    to_address = to_address + "@" + domain

                to_partner = self.env['res.partner'].search([('sip_address','=', to_address)])

            if to_partner:
                #Use the first found partner
                create_dict['to_partner_id'] = to_partner[0].id
            create_dict['to_address'] = to_address

            #Have to map the Twilio call status to the one in the core module
            twilio_status = call['status']
            if twilio_status == "queued":
                create_dict['status'] = "pending"
            elif twilio_status == "ringing":
                create_dict['status'] = "pending"
            elif twilio_status == "in-progress":
                create_dict['status'] = "active"
            elif twilio_status == "canceled":
                create_dict['status'] = "cancelled"
            elif twilio_status == "completed":
                create_dict['status'] = "over"
            elif twilio_status == "failed":
                create_dict['status'] = "failed"
            elif twilio_status == "busy":
                create_dict['status'] = "busy"
            elif twilio_status == "no-answer":
                create_dict['status'] = "failed"

            create_dict['start_time'] = call['start_time']
            create_dict['end_time'] = call['end_time']

            create_dict['twilio_sid'] = call['sid']
            #Duration includes the ring time
            create_dict['duration'] = call['duration']
            self.env['voip.call'].create(create_dict)

            self.twilio_last_check_date = datetime.utcnow()

    @api.multi
    def generate_invoice_previous_month(self):
        self.ensure_one()

        if self.partner_id.id == False:
            raise UserError("Please select a contact before creating the invoice")
            return False

        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/Usage/Records/LastMonth.json", auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
        json_usage_list = json.loads(response_string.text)

        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner_id.id,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'fiscal_position_id': self.partner_id.property_account_position_id.id,
        })

        _logger.error( response_string.text )
        start_date_string = json_usage_list['usage_records'][0]['start_date']
        end_date_string = json_usage_list['usage_records'][0]['end_date']
        invoice.comment = "Twilio Bill " + start_date_string + " - " + end_date_string

        while True:

            for usage_record in json_usage_list['usage_records']:
                category = usage_record['category']

                #Exclude the umbrella categories otherwise the pricing will overlap
                if float(usage_record['price']) > 0 and category != "calls" and category != "sms" and category != "phonenumbers" and category != "recordings" and category != "transcriptions" and category != "trunking-origination" and category != "totalprice":

                    line_values = {
                        'name': usage_record['description'],
                        'price_unit': float(usage_record['price']) * self.margin,
                        'invoice_id': invoice.id,
                        'account_id': invoice.journal_id.default_credit_account_id.id
                    }

                    invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
                
                    invoice.compute_taxes()

                #For debugging
                if category == "totalprice":
                    invoice.comment = invoice.comment + " (Total $" + usage_record['price'] + " USD) (Marign: $" + str(float(usage_record['price']) * self.margin) + " USD)"
                    _logger.error(usage_record['price'])             

            #Get the next page if there is one
            next_page_uri = json_usage_list['next_page_uri']
            if next_page_uri:
                response_string = requests.get("https://api.twilio.com" + next_page_uri, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
                json_usage_list = json.loads(response_string.text)
            else:
                #End the loop if there are is no more pages
                break

        #Also generate a call log report
        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/Calls.json?StartTime%3E=" + start_date_string + "&EndTime%3C=" + end_date_string, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
        json_call_list = json.loads(response_string.text)

        #Loop through all pages until you have reached the end
        call_total = 0
        while True:

            for call in json_call_list['calls']:
                if call['price']:
                    if float(call['price']) != 0:
                        #Format the date depending on the language of the contact
                        call_start = parser.parse(call['start_time'])
                        call_cost = -1.0 * float(call['price']) * self.margin
                        call_total += call_cost

                        m, s = divmod( int(call['duration']) , 60)
                        h, m = divmod(m, 60)
                        self.env['account.invoice.voip.history'].create({'invoice_id': invoice.id, 'start_time': call_start, 'duration': "%d:%02d:%02d" % (h, m, s), 'cost':  call_cost, 'to_address': call['to'] })

            #Get the next page if there is one
            next_page_uri = json_call_list['next_page_uri']
            if next_page_uri:
                response_string = requests.get("https://api.twilio.com" + next_page_uri, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
                json_call_list = json.loads(response_string.text)
            else:
                #End the loop if there are is no more pages
                break
              
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'res_id': invoice.id,
            'view_id': self.env['ir.model.data'].get_object('account', 'invoice_form').id
         }

class VoipTwilioInvoice(models.Model):

    _name = "voip.twilio.invoice"
    _description = "Twilio Account Invoice"

    twilio_account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    margin = fields.Float(string="Margin")

    @api.multi
    def generate_invoice(self):
        self.ensure_one()

        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_id.twilio_account_sid + "/Calls.json?StartTime%3E=" + self.start_date + "&EndTime%3C=" + self.end_date, auth=(str(self.twilio_account_id.twilio_account_sid), str(self.twilio_account_id.twilio_auth_token)))
        json_call_list = json.loads(response_string.text)

        invoice = self.env['account.invoice'].create({
            'partner_id': self.twilio_account_id.partner_id.id,
            'account_id': self.twilio_account_id.partner_id.property_account_receivable_id.id,
            'fiscal_position_id': self.twilio_account_id.partner_id.property_account_position_id.id,
        })

        #Loop through all pages until you have reached the end
        call_total = 0
        while True:

            for call in json_call_list['calls']:
                if call['price']:
                    if float(call['price']) != 0:
                        #Format the date depending on the language of the contact
                        call_start = parser.parse(call['start_time'])
                        call_cost = -1.0 * float(call['price']) * self.margin
                        call_total += call_cost

                        m, s = divmod( int(call['duration']) , 60)
                        h, m = divmod(m, 60)
                        self.env['account.invoice.voip.history'].create({'invoice_id': invoice.id, 'start_time': call_start, 'duration': "%d:%02d:%02d" % (h, m, s), 'cost':  call_cost, 'to_address': call['to'] })

            #Get the next page if there is one
            next_page_uri = json_call_list['next_page_uri']
            if next_page_uri:
                response_string = requests.get("https://api.twilio.com" + next_page_uri, auth=(str(self.twilio_account_id.twilio_account_sid), str(self.twilio_account_id.twilio_auth_token)))
                json_call_list = json.loads(response_string.text)
            else:
                #End the loop if there are is no more pages
                break

        line_values = {
            'name': "VOIP Calls " + self.start_date + " - " + self.end_date,
            'price_unit': call_total,
            'invoice_id': invoice.id,
            'account_id': invoice.journal_id.default_credit_account_id.id
        }

        invoice.write({'invoice_line_ids': [(0, 0, line_values)]})

        invoice.compute_taxes()

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'res_id': invoice.id,
            'view_id': self.env['ir.model.data'].get_object('account', 'invoice_form').id
         }

class AccountInvoiceVoip(models.Model):

    _inherit = "account.invoice"

    voip_history_ids = fields.One2many('account.invoice.voip.history', 'invoice_id', string="VOIP Call History")

class AccountInvoiceVoipHistory(models.Model):

    _name = "account.invoice.voip.history"
    _description = "Twilio Account Invoice History"

    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    start_time = fields.Datetime(string="Start Time")
    duration = fields.Char(string="Duration")
    to_address = fields.Char(string="To Address")
    cost = fields.Float(string="Cost")