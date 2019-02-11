# -*- coding: utf-8 -*

import logging
_logger = logging.getLogger(__name__)

from odoo import api, models
import odoo

class IrModuleModuleAppStoreClient(models.Model):

    _inherit = "ir.module.module"

    def restart_service(self):
        _logger.error("start core restart")
        odoo.service.server.restart()
        _logger.error("end core restart")