# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

from ..helpers import MONTH_LIST


class KaHrPayrollRapelScalePeriod(models.Model):
    """Data of rapel scale period. It can be base salary scale, or allowance scale.

    _name = 'ka_hr_payroll.rapel.scale.period'
    """

    _name = 'ka_hr_payroll.rapel.scale.period'

    SCALE_TYPE_NAME = [
        ('gp', "Gaji Pokok"),
        ('tr', "Tunj. Rumah"),
        ('tj', "Tunj. Jabatan"),
    ]

    name = fields.Char(string="Nama Rapel", size=255)
    new_period_id = fields.Many2one('ka_hr_payroll.scale.period', string="Ref. Periode Baru",
                                    readonly=True, ondelete='cascade')
    scale_type = fields.Selection(SCALE_TYPE_NAME, string="Tipe", related='new_period_id.scale_type',
                                  readonly=True, store=True)
    old_period_id = fields.Many2one('ka_hr_payroll.scale.period', string="Ref. Periode Lama", readonly=True)
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
    status_id = fields.Many2one('hr.status', string="Status Karyawan", related='new_period_id.status_id',
                                readonly=True, store=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='new_period_id.company_payroll_id', readonly=True, store=True)

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
        rapel_period = super(KaHrPayrollRapelScalePeriod, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            rapel_period.name = "Rapel {0}".format(rapel_period.new_period_id.name)
        return rapel_period

    @api.multi
    def _compute_rapel_text(self):
        for rapel in self:
            rapel.rapel_pay = '{0} {1}'.format(MONTH_LIST[rapel.month_pay - 1][1], rapel.year_pay)

    def get_approved_rapel_scale_period(self, scale_type, year_pay, month_pay, status_id, company_payroll_id):
        """Classmethod. Can call without instantiate.
        To get approved rapel.

        Arguments:
            scale_type {String} -- Type of scale. It can be 'gp', 'tr' or 'tj'.
            year_pay {String} -- Year of rapel pay.
            month_pay {Int} -- Month index of rapel pay.
            status_id {Int} -- ID of `hr.status`.
            company_payroll_id {Int} -- ID of `res.company`.

        Returns:
            Recordset -- Result of search approved rapel.
        """
        return self.search([
            ('scale_type', '=', scale_type),
            ('year_pay', '=', year_pay),
            ('month_pay', '=', month_pay),
            ('status_id', 'child_of', status_id),
            ('state', '=', 'approved'),
            ('company_payroll_id', '=', company_payroll_id),
        ])

    @api.multi
    def action_done(self, payroll):
        """To set `payroll_id` and set `state = 'done'`

        Arguments:
            payroll {Recordset} -- Recordset from `ka_hr_payroll.payroll`.
        """
        self.payroll_id = payroll
        self.date_done = payroll.date_payroll
        self.state = 'done'

    @api.multi
    def action_view_rapel_scale(self):
        """To view all `ka_hr_payroll.rapel.scale` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        action = self.env.ref('ka_hr_payroll.action_rapel_scale')
        result = action.read()[0]
        result['domain'] = [('rapel_period_id', '=', self.id)]
        result['context'] = {'default_rapel_period_id': self.id}
        return result


class KaHrPayrollRapelScale(models.Model):
    """Data of rapel based from `ka_hr_payroll.scale`.

    _name = 'ka_hr_payroll.rapel.scale'
    """

    _name = 'ka_hr_payroll.rapel.scale'

    name = fields.Char(string="Nama Rapel Skala", size=255)
    rapel_period_id = fields.Many2one('ka_hr_payroll.rapel.scale.period', string="Rapel Periode", required=True,
                                      readonly=True, ondelete='cascade')
    new_scale_id = fields.Many2one('ka_hr_payroll.scale', string="Ref. Skala Baru", required=True,
                                   readonly=True)
    old_scale_id = fields.Many2one('ka_hr_payroll.scale', string="Ref. Skala Lama", readonly=True)
    state = fields.Selection([
        ('approved', "Disetujui"),
        ('done', "Proses Selesai"),
    ], string="Status", related='rapel_period_id.state', readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='rapel_period_id.company_payroll_id', readonly=True)
    line_ids = fields.One2many('ka_hr_payroll.rapel.scale.lines', 'rapel_scale_id', readonly=True)

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
        rapel_scale = super(KaHrPayrollRapelScale, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            rapel_scale.name = "Rapel {0}".format(rapel_scale.new_scale_id.name)
        return rapel_scale


class KaHrPayrollRapelScaleLines(models.Model):
    """Data lines of rapel scale.

    _name = 'ka_hr_payroll.rapel.scale.lines'
    """

    _name = 'ka_hr_payroll.rapel.scale.lines'

    rapel_scale_id = fields.Many2one('ka_hr_payroll.rapel.scale', string="Rapel Skala", readonly=True,
                                     ondelete='cascade')
    new_scale_lines_id = fields.Many2one('ka_hr_payroll.scale.lines', string="Ref. Skala Baru",
                                         readonly=True)
    old_scale_lines_id = fields.Many2one('ka_hr_payroll.scale.lines', string="Ref. Skala Lama", readonly=True)
    scale = fields.Float(string="Skala", digits=(6, 3), readonly=True)
    new_value = fields.Float(string="Nilai Baru", default=0.0, readonly=True)
    old_value = fields.Float(string="Nilai Lama", default=0.0, readonly=True)
    selisih = fields.Float(compute='_compute_selisih', string="Selisih", readonly=True)

    @api.depends('old_value', 'new_value')
    def _compute_selisih(self):
        """To compute `selisih`.

        Decorators:
            @api.depends('old_value', 'new_value')
        """
        for line in self:
            if line.old_value and line.new_value:
                line.selisih = abs(line.new_value - line.old_value)
