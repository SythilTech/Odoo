# -*- coding: utf-8 -*-
import time
from openerp import api, models, _

import logging
_logger = logging.getLogger(__name__)

class ReportWebsetAupportAnalyticTimesheetsSupportTechReport(models.Model):

    _name = "report.webset_support_analytic_timesheets.support_tech_report"

    @api.multi
    def render_html(self, data):
    
        _logger.error("Render HTML Support Tech")
        
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'test': 'hello',
        }
        
        return self.env['report'].render('website_support_analytics_timesheets.support_tech_report_template', docargs)
