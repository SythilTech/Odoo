# -*- coding: utf-8 -*
from openerp import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class ViewInheritVersioning(models.Model):

    _inherit = "ir.ui.view"

    version_id = fields.Many2one('website.ver', string="Version")

    @api.multi
    def write(self, values, context=None):
        
        update_rec = super(ViewInheritVersioning, self).write(values)

        if 'arch' in values:
            if self.version_id:
                self.version_id.arch_base = values['arch']

        return update_rec

    @api.one
    @api.onchange('version_id')
    def _onchange_version_id(self):
        if self.version_id:
            self.arch_base = self.version_id.arch_base

class WebsiteVer(models.Model):

    _name = "website.ver"
    _description = "Website Version"

    name = fields.Char(string="Name")
    arch_base = fields.Text(string="Arch")