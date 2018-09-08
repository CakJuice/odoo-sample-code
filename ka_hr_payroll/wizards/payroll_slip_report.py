# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

from ..helpers import MONTH_LIST, YEAR_LIST


class KaHrPayrollSlipReportWizard(models.TransientModel):
    """Wizard used to create payroll slip report.

    _name = 'ka_hr_payroll.slip.report.wizard'
    """

    _name = 'ka_hr_payroll.slip.report.wizard'

    year_period = fields.Selection(YEAR_LIST, string="Tahun Periode", required=True,
                                   default=datetime.now().year)
    month_period = fields.Selection(MONTH_LIST, string="Bulan Periode", required=True,
                                    default=datetime.now().month)
    type_slip = fields.Selection([
        ('1', "Cetak Per Karyawan"),
        ('2', "Cetak Per Unit/PG"),
        ('3', "Cetak Per Lokasi Penggajian")
    ], string="Tipe Cetak Slip", default='1', required=True)
    employee_id = fields.Many2one('hr.employee', string="Karyawan")
    status_id = fields.Many2one('hr.status', string="Status Karyawan")
    company_id = fields.Many2one('res.company', string="Unit/PG", default=lambda self: self.env.user.company_id)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         default=lambda self: self.env.user.company_id)

    @api.multi
    def generate_report(self):
        """To generate report. Call from button.
        """
        docids = []
        if self.type_slip == '1':
            payroll = self.env['ka_hr_payroll.payroll.employee'].search([
                ('payroll_year_period', '=', self.year_period),
                ('payroll_month_period', '=', self.month_period),
                ('employee_id', '=', self.employee_id.id)
            ], limit=1)
            if payroll:
                docids = payroll.ids
        else:
            payroll = self.env['ka_hr_payroll.payroll'].search([
                ('year_period', '=', self.year_period),
                ('month_period', '=', self.month_period),
                ('employee_status_id', 'child_of', self.status_id.id),
                ('company_payroll_id', '=', self.company_payroll_id.id),
            ], limit=1)
            if payroll:
                if self.type_slip == '2':
                    employee_ids = payroll.payroll_employee_ids
                    filtered = employee_ids.filtered(lambda r: r.employee_id.company_id == self.company_id)
                    docids = filtered.ids
                else:
                    docids = payroll.payroll_employee_ids.ids
        if docids:
            return self.env['report'].get_action(docids, 'ka_hr_payroll.payroll_slip_report_view')
        else:
            raise UserError("Data penggajian tidak ditemukan!")
