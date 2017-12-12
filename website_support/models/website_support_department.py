# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportDepartment(models.Model):

    _name = "website.support.department"
    
    name = fields.Char(string="Name", translate=True)
    manager_ids = fields.One2many('website.support.department.contact', 'wsd_id', string="Managers")
    partner_ids = fields.Many2many('res.partner', string="Contacts")
    sub_category_ids = fields.One2many('website.support.department.subcategory', 'wsd_id', string="Sub Categories", compute='_compute_sub_category_ids')

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_sub_category_ids(self):
        
        #Unlink all existing records
        for si in self.env['website.support.department.subcategory'].search([('wsd_id', '=', self.id)]):
            si.unlink()
            
        extra_access = []
        for extra_permission in self.partner_ids:
            extra_access.append(extra_permission.id)
        
        support_tickets = self.env['website.support.ticket'].sudo().search(['|', ('partner_id','=', self.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False) ])        

        for sub_category in self.env['website.support.ticket.subcategory'].search([]):
            count = self.env['website.support.ticket'].search_count(['|', ('partner_id','=', self.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False), ('sub_category_id','=', sub_category.id)])
            if count > 0:
                self.env['website.support.department.subcategory'].create( {'wsd_id': self.id, 'subcategory_id': sub_category.id, 'count': count} )
            
        self.sub_category_ids = self.env['website.support.department.subcategory'].search([('wsd_id', '=', self.id)])
        
class WebsiteSupportDepartmentContact(models.Model):

    _name = "website.support.department.contact"

    def _default_role(self):
        return self.env['ir.model.data'].get_object('website_support','website_support_department_manager')

    wsd_id = fields.Many2one('website.support.department', string="Department")
    role = fields.Many2one('website.support.department.role', string="Role", required="True", default=_default_role)
    user_id = fields.Many2one('res.users', string="User", required="True")

class WebsiteSupportDepartmentRole(models.Model):

    _name = "website.support.department.role"

    name = fields.Char(string="Name", translate=True)
    view_department_tickets = fields.Boolean(string="View Department Tickets")
    
class WebsiteSupportDepartmentSubcategory(models.Model):

    _name = "website.support.department.subcategory"
    _order = "count desc"

    wsd_id = fields.Many2one('website.support.department', string="Department")
    subcategory_id = fields.Many2one('website.support.ticket.subcategory', string="Sub Category")
    count = fields.Integer(string="Count")