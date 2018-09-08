# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

from ..helpers import MONTH_LIST


class KaHrPayrollRapelTunjanganKhususPeriod(models.Model):
    """Data of rapel based from `ka_hr_payroll.tunjangan.khusus.period`.

    _name = 'ka_hr_payroll.rapel.tunjangan.khusus.period'
    """

    _name = 'ka_hr_payroll.rapel.tunjangan.khusus.period'

    name = fields.Char(string="Nama Rapel", size=255)
    new_period_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.period',
                                    string="Ref. Tunj. Khusus Baru", readonly=True, ondelete='cascade')
    old_period_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.period',
                                    string="Ref. Tunj. Khusus Lama", readonly=True)
    date_start = fields.Datetime(string="Tanggal Mulai Rapel", readonly=True)
    date_end = fields.Datetime(string="Tanggal Akhir Rapel", readonly=True)
    year_pay = fields.Char(string="Tahun Bayar Rapel", size=4, readonly=True)
    month_pay = fields.Selection(MONTH_LIST, string="Bulan Bayar Rapel", readonly=True)
    rapel_pay = fields.Char(string="Bayar Rapel", compute='_compute_rapel_text')
    status_id = fields.Many2one('hr.status', string="Status Karyawan",
                                related='new_period_id.status_id', readonly=True, store=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='new_period_id.company_payroll_id', readonly=True, store=True)
    state = fields.Selection([
        ('approved', "Disetujui"),
        ('done', "Proses Selesai"),
    ], string="Status", default='approved', readonly=True)
    date_done = fields.Date(string="Tanggal Diproses", readonly=True)
    payroll_id = fields.Many2one('ka_hr_payroll.payroll', string="Referensi Penggajian", readonly=True)
    line_ids = fields.One2many('ka_hr_payroll.rapel.tunjangan.khusus.period.lines', 'rapel_period_id',
                               string="Detail Rapel", readonly=True)

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
        rapel = super(KaHrPayrollRapelTunjanganKhususPeriod, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            rapel.name = "Rapel {0}".format(rapel.new_period_id.name)
        return rapel

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

    def get_approved_rapel(self, year_pay, month_pay, status_id, company_payroll_id):
        """Classmethod. Can call without instantiate.
        To get approved rapel.

        Arguments:
            year_pay {String} -- Year of rapel pay.
            month_pay {Int} -- Month index of rapel pay.
            status_id {Int} -- ID of `hr.status`.
            company_payroll_id {Int} -- ID of `res.company`.

        Returns:
            Recordset -- Result of search approved rapel.
        """
        return self.search([
            ('year_pay', '=', year_pay),
            ('month_pay', '=', month_pay),
            ('status_id', 'child_of', status_id),
            ('state', '=', 'approved'),
            ('company_payroll_id', '=', company_payroll_id),
        ])


class KaHrPayrollRapelTunjanganKhususPeriodLines(models.Model):
    """Data lines of rapel tunjangan khusus.

    _name = 'ka_hr_payroll.rapel.tunjangan.khusus.period.lines'
    """

    _name = 'ka_hr_payroll.rapel.tunjangan.khusus.period.lines'

    rapel_period_id = fields.Many2one('ka_hr_payroll.rapel.tunjangan.khusus.period', string="Rapel Periode",
                                      readonly=True, ondelete='cascade')
    new_period_lines_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.period.lines',
                                          string="Ref. Detail Baru", readonly=True)
    old_period_lines_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.period.lines',
                                          string="Ref. Detail Lama", readonly=True)
    combine_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.combine', string="Penerima",
                                 related='new_period_lines_id.combine_id', readonly=True, store=True)
    new_value = fields.Float(string="Nilai Baru", default=0.0, readonly=True)
    old_value = fields.Float(string="Nilai Lama", default=0.0, readonly=True)
    selisih = fields.Float(compute='_compute_selisih', string="Selisih", readonly=True)

    @api.depends('new_value', 'old_value')
    def _compute_selisih(self):
        for periode in self:
            if periode.old_value and periode.new_value:
                periode.selisih = abs(periode.new_value - periode.old_value)
