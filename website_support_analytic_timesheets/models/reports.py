# -*- coding: utf-8 -*-
import time
from openerp import api, models, _

import logging
_logger = logging.getLogger(__name__)

class ReportWebsetAupportAnalyticTimesheetsSupportTechReport(models.Model):

    _name = "report.website_support_analytic_timesheets.strt"

    @api.multi
    def get_report_values(self, docids, data=None):
        docs = self.env['account.analytic.line'].browse(docids)


        date_dict = {}
        for timesheet_line in docs:
            #Group by Date
            if str(timesheet_line.date) not in date_dict:
                date_dict[str(timesheet_line.date)] = {}

            #Sub group by employee name
            if str(timesheet_line.employee_id.name) not in date_dict[str(timesheet_line.date)]:
                date_dict[str(timesheet_line.date)][str(timesheet_line.employee_id.name)] = []
            
            date_dict[str(timesheet_line.date)][str(timesheet_line.employee_id.name)].append(timesheet_line)

        _logger.error(date_dict)

        return {
            'doc_model': 'account.analytic.line',
            'docs': date_dict
        }