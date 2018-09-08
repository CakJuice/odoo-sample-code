# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

from ..helpers import MONTH_LIST


class KaHrPayrollRapelEmployeePromote(models.Model):
    """Data rapel of `hr.employee.promote`.

    _name = 'ka_hr_payroll.rapel.hr.employee.promote'
    """

    _name = 'ka_hr_payroll.rapel.hr.employee.promote'

    name = fields.Char(string="Nama Rapel", size=255)
    new_employee_promote_id = fields.Many2one('hr.employee.promote', string="Ref. History Karyawan Baru",
                                              readonly=True, ondelete='cascade')
    old_employee_promote_id = fields.Many2one('hr.employee.promote', string="Ref. History Karyawan Lama",
                                              readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Karyawan", related='new_employee_promote_id.employee_id',
                                  readonly=True, store=True)
    date_start = fields.Datetime(string="Tanggal Mulai Rapel", readonly=True)
    date_end = fields.Datetime(string="Tanggal Akhir Rapel", readonly=True)
    year_pay = fields.Char(string="Tahun Bayar Rapel", size=4, readonly=True)
    month_pay = fields.Selection(MONTH_LIST, string="Bulan Bayar Rapel", readonly=True)
    rapel_pay = fields.Char(string="Bayar Rapel", compute='_compute_rapel_text')
    state = fields.Selection([
        ('approved', "Disetujui"),
        ('done', "Proses Selesai"),
    ], string="Status", default='approved', readonly=True)
    date_done = fields.Date(string="Tanggal Diproses", readonly=True)
    payroll_id = fields.Many2one('ka_hr_payroll.payroll', string="Referensi Penggajian", readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='new_employee_promote_id.company_payroll_id', required=True,
                                         store=True)

    @api.model
    def create(self, vals):
        """Override method `create()`. Use for insert data

        Decorators:
			api.model

        Arguments:
            vals {Dict} -- Values insert data

        Returns:
			Recordset -- Create result will return recordset
        """
        record = super(KaHrPayrollRapelEmployeePromote, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            record.name = "Rapel {0}".format(record.new_employee_promote_id.name)
        return record

    @api.multi
    def _compute_rapel_text(self):
        for rapel in self:
            rapel.rapel_pay = '{0} {1}'.format(MONTH_LIST[rapel.month_pay - 1][1], rapel.year_pay)

    def action_done(self, payroll):
        """To set `payroll_id` and set `state = 'done'`

        Arguments:
            payroll {Recordset} -- Recordset from `ka_hr_payroll.payroll`.
        """
        self.payroll_id = payroll
        self.date_done = payroll.date_payroll
        self.state = 'done'

    def get_employee_rapel_pay(self, employee_id, year_pay, month_pay):
        """To get recordset of rapel based on employee and pay period.

        Arguments:
            employee_id {Recordset} -- ID of `hr.employee`.
            year_pay {String} -- Year period of rapel pay.
            month_pay {Int} -- Month period of rapel pay.

        Returns:
            Recordset -- Result of rapel searching.
        """
        return self.search([
            ('year_pay', '=', year_pay),
            ('month_pay', '=', month_pay),
            ('employee_id', '=', employee_id),
        ])
