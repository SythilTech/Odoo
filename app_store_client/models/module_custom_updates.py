# -*- coding: utf-8 -*
import logging
_logger = logging.getLogger(__name__)
import json
import requests

from openerp import api, fields, models

class ModuleCustomUpdates(models.Model):

    _name = "module.custom.updates"

    name = fields.Char(string="Name")
    shortdesc = fields.Char(string="Short Description")
    installed_version = fields.Char(string="Current Version")
    latest_version = fields.Char(string="Lastest Version")
    changelog = fields.Text(string="Changelog")


    def custom_module_update_download(self):
        _logger.error("Update Module")

    @api.multi
    def check_custom_app_store_updates(self):
        self.ensure_one()

        _logger.error("Check for custom updates")

        for up_md in self.env['module.custom.updates'].search([]):
            up_md.unlink()
        
        custom_app_store_url = self.env['ir.config_parameter'].get_param('custom_app_store_url') 

        r = requests.get(custom_app_store_url + "/custom/store/updates")
        module_list = json.loads(r.content.decode('utf-8'))
        
        for md in module_list:
            local_md = self.env['ir.module.module'].search([('name','=', md['name']), ('state','=','installed')])
            if local_md:
                _logger.error(local_md.installed_version)
                _logger.error(md['latest_version'])
                if local_md.installed_version != md['latest_version']:
                    self.env['module.custom.updates'].create({'name': md['name'], 'shortdesc': local_md.shortdesc, 'installed_version': local_md.installed_version, 'latest_version': md['latest_version']})

        return {
            'name': 'Updatable Modules',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'module.custom.updates',
            'type': 'ir.actions.act_window',
         }