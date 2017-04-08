from openerp import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class art_user_gf(models.Model):

    _inherit = "res.users"

    art_gf = fields.Boolean(string="Artificial Girlfriend")