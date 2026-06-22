from odoo import api, models, _
from odoo.exceptions import UserError
import datetime


class ReportAccountSST(models.AbstractModel):
    _name = 'report.sst_reports.report_sst'


    def _get_report_values(self, docids, data=None):
        print(data)
        docargs = {
            'doc_ids': data['form']['doc_ids'],
            # 'doc_model': report.model,
            'docs': self,
        }
        return docargs

