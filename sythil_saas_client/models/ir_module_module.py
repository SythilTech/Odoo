from openerp import models, api, fields, exceptions, SUPERUSER_ID

MODULE_NAME = 'sythil_saas_client'

class Module(models.Model):

    _inherit = "ir.module.module"

    def button_uninstall(self, cr, uid, ids, context=None):
        for r in self.browse(cr, uid, ids):
            if r.name == MODULE_NAME and uid != SUPERUSER_ID:
                raise exceptions.Warning("Only admin can uninstall the module")
        return super(Module, self).button_uninstall(cr, uid, ids, context=context)