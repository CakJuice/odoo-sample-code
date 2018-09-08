# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

from ..helpers import MONTH_LIST


class KaHrPayrollRapelCompanyKonjungtur(models.Model):
    """Data of rapel company konjungtur.

    _name = 'ka_hr_payroll.rapel.company.konjungtur'
    """

    _name = 'ka_hr_payroll.rapel.company.konjungtur'
    _description = "Rapel Set Unit/PG Konjungtur Gaji / Dapen"

    _KONJUNGTUR_TYPE_NAME = [
        ('1', "Konjungtur Gaji"),
        ('2', "Konjungtur Dapen"),
    ]

    name = fields.Char(string="Nama Rapel", size=255)
    new_konjungtur_id = fields.Many2one('ka_hr_payroll.company.konjungtur', string="Ref. Konjungtur Baru",
                                        readonly=True, ondelete='cascade')
    old_konjungtur_id = fields.Many2one('ka_hr_payroll.company.konjungtur', string="Ref. Konjungtur Lama",
                                        readonly=True)
    konjungtur_type = fields.Selection(_KONJUNGTUR_TYPE_NAME, string="Tipe",
                                       related='new_konjungtur_id.konjungtur_type', readonly=True, store=True)
    date_start = fields.Datetime(string="Tanggal Mulai Rapel", readonly=True)
    date_end = fields.Datetime(string="Tanggal Akhir Rapel", readonly=True)
    year_pay = fields.Char(string="Tahun Bayar Rapel", size=4, readonly=True)
    month_pay = fields.Selection(MONTH_LIST, string="Bulan Bayar Rapel", readonly=True)
    rapel_pay = fields.Char(string="Bayar Rapel", compute='_compute_rapel_text')
    new_value = fields.Float(string="Nilai Baru (%)", readonly=True, default=0.0)
    old_value = fields.Float(string="Nilai Lama (%)", readonly=True, default=0.0)
    state = fields.Selection([
        ('approved', "Disetujui"),
        ('done', "Proses Selesai"),
    ], string="Status", default='approved', readonly=True)
    date_done = fields.Date(string="Tanggal Diproses", readonly=True)
    payroll_id = fields.Many2one('ka_hr_payroll.payroll', string="Referensi Penggajian", readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='new_konjungtur_id.company_payroll_id', readonly=True, store=True)

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
        rapel = super(KaHrPayrollRapelCompanyKonjungtur, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            rapel.name = "Rapel {0}".format(rapel.new_konjungtur_id.name)
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

    def get_approved_rapel(self, year_pay, month_pay, company_payroll_id):
        """Classmethod. Can call without instantiate.
        To get approved rapel.

        Arguments:
            year_pay {String} -- Year of rapel pay.
            month_pay {Int} -- Month index of rapel pay.
            company_payroll_id {Int} -- ID of `res.company`.

        Returns:
            Recordset -- Result of search approved rapel.
        """
        return self.search([
            ('year_pay', '=', year_pay),
            ('month_pay', '=', month_pay),
            ('state', '=', 'approved'),
            ('company_payroll_id', '=', company_payroll_id),
        ])
