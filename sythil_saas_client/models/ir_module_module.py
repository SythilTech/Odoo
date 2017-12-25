from openerp import models, api, fields, exceptions, SUPERUSER_ID

class Module(models.Model):

    _inherit = "ir.module.module"

    @api.multi
    def button_uninstall(self):
        for r in self:
            if r.name == 'sythil_saas_client' and self.env.user.id != SUPERUSER_ID:
                raise exceptions.Warning("Only admin can uninstall the module")
        return super(Module, self).button_uninstall()