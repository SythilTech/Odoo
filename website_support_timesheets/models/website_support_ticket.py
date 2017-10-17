# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritTimesheets(models.Model):

    _inherit = "website.support.ticket"
    
    timesheet_ids = fields.One2many('website.support.ticket.timesheet', 'wst_id', string="Timesheet")

    @api.multi
    def invoice_client(self):
        self.ensure_one()

        invoiced_state = self.env['ir.model.data'].sudo().get_object('website_support_timesheets', 'website_ticket_state_invoiced')
        self.state = invoiced_state
 
        invoice_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1).id
        new_invoice = self.env['account.invoice'].create({'name': '', 'type': 'out_invoice', 'partner_id': self.partner_id.id, 'account_id': invoice_account, 'comment': 'Support Ticket #' + str(self.id) + " " + self.subject.encode("UTF-8") })
        
        for timesheet in self.timesheet_ids:
            time_string = ""
            
            if timesheet.hours == 1:
                time_string += "1 hour"
            else:
                time_string += str(timesheet.hours) + " hours"

            time_string += " and "

            if timesheet.minutes == 1:
                time_string += "1 minute"
            else:
                time_string += str(timesheet.minutes) + " minutes"            
            
            new_invoice.invoice_line_ids.create({'invoice_id': new_invoice.id, 'name': 'Support Ticket Service (' + time_string + ')', 'account_id': invoice_account, 'price_unit': '0'})
            
        return {
	            'name':"Support Ticket Invoice",
	            'view_mode': 'form',
	            'view_type': 'form',
	            'res_model': 'account.invoice',
	            'type': 'ir.actions.act_window',
	            'res_id': new_invoice.id,
	        }
    
class WebsiteSupportTicketTimesheet(models.Model):

    _name = "website.support.ticket.timesheet"
    
    wst_id = fields.Many2one('website.support.ticket', string="Support Ticket")
    ticket_description = fields.Text(related="wst_id.description", string="Description")
    hours = fields.Integer(string="Hours")
    minutes = fields.Integer(sring="Minutes")
    project_id = fields.Many2one('project.project', string="Project")
    ticket_number_display = fields.Char(related="wst_id.ticket_number_display", string="Support Ticket Number")
    state = fields.Many2one('website.support.ticket.states', readonly=True, related="wst_id.state", string="State")
    open_time = fields.Datetime(related="wst_id.create_date", string="Open Time")
    close_time = fields.Datetime(related="wst_id.close_time", string="Close Time")