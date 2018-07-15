# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import datetime

from openerp import api, fields, models, tools

class ResPartnerSupportBilling(models.Model):

    _inherit = "res.partner"

    @api.multi
    def support_billing_action(self):
        self.ensure_one()

        return {
            'name': 'Support Billing Invoice Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner.support.billing.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_partner_id': self.id}
        }

class ResPartnerSupportBillingWizard(models.Model):

    _name = "res.partner.support.billing.wizard"

    partner_id = fields.Many2one('res.partner', string="Partner")
    start_date = fields.Date(string="Start Date", required="True")
    end_date = fields.Date(string="End Date", required="True")
    per_hour_charge = fields.Float(string="Per Hour Charge")

    @api.multi
    def generate_invoice(self):
        self.ensure_one()

        new_invoice = self.env['account.invoice'].create({
            'partner_id': self.partner_id.id,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'fiscal_position_id': self.partner_id.property_account_position_id.id,
        })

        if self.partner_id.company_type == "person":

            #Get all the invoice lines for just a single individual
            self.partner_ticket_task_charge(new_invoice, self.partner_id)

        elif self.partner_id.company_type == "company":

            #Loop through all contacts and get the invoice lines
            for company_contact in self.partner_id.child_ids:
                self.partner_ticket_task_charge(new_invoice, company_contact)

        new_invoice.compute_taxes()

        return {
            'name': 'Support Billing Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'res_id': new_invoice.id
        }

    def partner_ticket_task_charge(self, new_invoice, partner):

        partner_tasks = self.env['project.task'].search([('partner_id','=', partner.id), ('create_date','>=',self.start_date), ('create_date','<=',self.end_date)])
        partner_tickets = self.env['website.support.ticket'].search([('partner_id','=', partner.id), ('create_date','>=',self.start_date), ('create_date','<=',self.end_date)])

        for support_ticket in partner_tickets:
            total_hours = 0

            for timesheet_line in support_ticket.analytic_timesheet_ids:
                total_hours += timesheet_line.unit_amount

            total_charge = total_hours * self.per_hour_charge

            line_values = {
                'name': support_ticket.subject,
                'price_unit': total_charge,
                'invoice_id': new_invoice.id,
                'account_id': new_invoice.journal_id.default_credit_account_id.id
            }

            new_invoice.write({'invoice_line_ids': [(0, 0, line_values)]})

        for task in partner_tasks:
            total_hours = 0

            for timesheet_line in task.timesheet_ids:
                total_hours += timesheet_line.unit_amount

            total_charge = total_hours * self.per_hour_charge

            line_values = {
                'name': task.name,
                'price_unit': total_charge,
                'invoice_id': new_invoice.id,
                'account_id': new_invoice.journal_id.default_credit_account_id.id
            }

            new_invoice.write({'invoice_line_ids': [(0, 0, line_values)]})