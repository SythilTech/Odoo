# -*- coding: utf-8 -*
import logging
_logger = logging.getLogger(__name__)
import json
import requests
import os
import zipfile
import urllib.request
import io

from odoo import api, fields, models, modules

class ModuleCustomUpdates(models.Model):

    _name = "module.custom.updates"

    name = fields.Char(string="Name")
    shortdesc = fields.Char(string="Short Description")
    installed_version = fields.Char(string="Current Version")
    latest_version = fields.Char(string="Lastest Version")
    changelog = fields.Text(string="Changelog")

    @api.multi
    def custom_module_update_download(self):
        self.ensure_one()
        _logger.error("Update Module")

        module_path = modules.get_module_path(self.name)

        app_store = self.env['ir.config_parameter'].get_param('custom_app_store_url')
        r = requests.get(app_store + "/apps/modules/download/" + self.name)

        zip_ref = zipfile.ZipFile(io.BytesIO(r.content))
        zip_ref.extractall(module_path)
        zip_ref.close()

        updated_module = self.env['ir.module.module'].search([('name','=',self.name)])[0]
        #updated_module.button_immediate_install()

        return {
            'name': 'Module',
            'view_mode': 'form',
            'view_type': 'kanban,tree,form',
            'res_model': 'ir.module.module',
            'res_id': updated_module.id,
            'type': 'ir.actions.act_window',
         }

    @api.multi
    def check_custom_app_store_updates(self):
        self.ensure_one()

        for up_md in self.env['module.custom.updates'].search([]):
            up_md.unlink()
        
        custom_app_store_url = self.env['ir.config_parameter'].get_param('custom_app_store_url')

        r = requests.get(custom_app_store_url + "/custom/store/updates")
        module_list = json.loads(r.content.decode('utf-8'))
        
        for md in module_list:
            local_md = self.env['ir.module.module'].search([('name','=', md['name']), ('state','=','installed')])
            if local_md:
                if local_md.installed_version != md['latest_version']:
                    self.env['module.custom.updates'].create({'name': md['name'], 'shortdesc': local_md.shortdesc, 'installed_version': local_md.installed_version, 'latest_version': md['latest_version']})

        return {
            'name': 'Updatable Modules',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'module.custom.updates',
            'type': 'ir.actions.act_window',
         }