# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

from ..helpers import MONTH_LIST


class KaHrPayrollRapelCompanyDefault(models.Model):
    """Data of rapel based from `ka_hr_payroll.rapel.company.default`.

    _name = 'ka_hr_payroll.rapel.company.default'
    """

    _name = 'ka_hr_payroll.rapel.company.default'
    _description = "Rapel untuk ketetapan gaji Unit/PG"

    name = fields.Char(string="Nama", size=255)
    new_company_default_id = fields.Many2one('ka_hr_payroll.company.default', string="Ref. Ketetapan Baru",
                                             readonly=True, ondelete='cascade')
    old_company_default_id = fields.Many2one('ka_hr_payroll.company.default', string="Ref. Ketetapan Lama",
                                             readonly=True)
    date_start = fields.Datetime(string="Tanggal Mulai Rapel", readonly=True)
    date_end = fields.Datetime(string="Tanggal Akhir Rapel", readonly=True)
    year_pay = fields.Char(string="Tahun Bayar Rapel", size=4, readonly=True)
    month_pay = fields.Selection(MONTH_LIST, string="Bulan Bayar Rapel", readonly=True)
    rapel_pay = fields.Char(string="Bayar Rapel", compute='_compute_rapel_text')
    new_gaji_pokok = fields.Float(string="Gaji Pokok Baru", readonly=True)
    new_tunjangan_rumah = fields.Float(string="Tunj. Rumah Baru", readonly=True)
    new_tunjangan_jabatan = fields.Float(string="Tunj. Jabatan Baru", readonly=True)
    new_tunjangan_khusus = fields.Float(string="Tunj. Khusus Baru", readonly=True)
    new_tunjangan_representasi = fields.Float(string="Tunj. Representasi Baru", readonly=True)
    old_gaji_pokok = fields.Float(string="Gaji Pokok Lama", readonly=True)
    old_tunjangan_rumah = fields.Float(string="Tunj. Rumah Lama", readonly=True)
    old_tunjangan_jabatan = fields.Float(string="Tunj. Jabatan Lama", readonly=True)
    old_tunjangan_khusus = fields.Float(string="Tunj. Khusus Lama", readonly=True)
    old_tunjangan_representasi = fields.Float(string="Tunj. Representasi Lama", readonly=True)
    state = fields.Selection([
        ('approved', "Disetujui"),
        ('done', "Proses Selesai"),
    ], string="Status", default='approved', readonly=True)
    date_done = fields.Date(string="Tanggal Diproses", readonly=True)
    status_id = fields.Many2one('hr.status', related='new_company_default_id.status_id',
                                string="Status Karyawan", readonly=True)
    payroll_id = fields.Many2one('ka_hr_payroll.payroll', string="Referensi Penggajian", readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='new_company_default_id.company_payroll_id', readonly=True, store=True)

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
        record = super(KaHrPayrollRapelCompanyDefault, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            record.name = "Rapel {0}".format(record.new_company_default_id.name)
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
