# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from ..helpers import datetime_to_local_date, format_local_currency


class KaHrPayrollHolidaysAfkoop(models.Model):
    """Data of employee's afkoop.

    _inherit = 'ka_hr.holidays.afkoop'
    """

    _inherit = 'ka_hr.holidays.afkoop'

    employee_gaji_pokok = fields.Float(string="Gaji Pokok", compute='_compute_total', store=True)
    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", compute='_compute_total', store=True)
    employee_tunjangan_rumah = fields.Float(string="Tunjangan Rumah", compute='_compute_total',
                                            store=True)
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", compute='_compute_total', store=True)
    employee_tunjangan_jabatan = fields.Float(string="Tunjangan Jabatan", compute='_compute_total',
                                              store=True)
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", compute='_compute_total', store=True)
    employee_tunjangan_khusus = fields.Float(string="Tunjangan Khusus", compute='_compute_total',
                                             store=True)
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", compute='_compute_total',
                                               store=True)
    employee_tunjangan_representasi = fields.Float(string="Tunjangan Representasi",
                                                   compute='_compute_total', store=True)
    konjungtur_gaji = fields.Float(string="Konjungtur Gaji (%)", compute='_compute_total', store=True)
    is_multiply_konjungtur = fields.Boolean(string="Dikalikan Konjungtur", compute='_compute_total', store=True)
    employee_gapok_total = fields.Float(string="Gaji Pokok Total", compute='_compute_total', store=True)
    total = fields.Float(string="Total", compute='_compute_total', store=True)
    total_multiply = fields.Float(string="Total", compute='_compute_total', store=True)
    company_payroll_id = fields.Many2one('res.company', compute='_compute_total', store=True)
    rapel_ref_ids = fields.One2many('ka_hr_payroll.payroll.afkoop.rapel', 'afkoop_rapel_ref_id',
                                    string="Ref. Pembayar Rapel", readonly=True)

    @api.depends('employee_id', 'jumlah')
    def _compute_total(self):
        config = self.env['ka_hr_payroll.config'].default_config()
        for afkoop in self:
            if not afkoop.employee_id or not afkoop.jumlah:
                continue

            employee = afkoop.employee_id
            afkoop.company_payroll_id = employee.company_payroll_id
            afkoop.employee_gaji_pokok = employee.gaji_pokok

            afkoop.is_tunjangan_rumah = employee.payroll_company_id.afkoop_tunjangan_rumah
            if afkoop.is_tunjangan_rumah:
                afkoop.employee_tunjangan_rumah = employee.tunjangan_rumah
            else:
                afkoop.employee_tunjangan_rumah = 0

            afkoop.is_tunjangan_jabatan = employee.payroll_company_id.afkoop_tunjangan_jabatan
            if afkoop.is_tunjangan_jabatan:
                afkoop.employee_tunjangan_jabatan = employee.tunjangan_jabatan
            else:
                afkoop.employee_tunjangan_jabatan = 0

            afkoop.is_tunjangan_khusus = employee.payroll_company_id.afkoop_tunjangan_khusus
            if afkoop.is_tunjangan_khusus:
                afkoop.employee_tunjangan_khusus = employee.tunjangan_khusus
            else:
                afkoop.employee_tunjangan_khusus = 0

            afkoop.is_tunjangan_representasi = employee.payroll_company_id.afkoop_tunjangan_representasi
            if afkoop.is_tunjangan_representasi:
                afkoop.employee_tunjangan_representasi = employee.tunjangan_representasi
            else:
                afkoop.employee_tunjangan_representasi = 0

            afkoop.is_multiply_konjungtur = employee.status_id.is_multiply_konjungtur
            if afkoop.is_multiply_konjungtur:
                last_konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                        afkoop.company_payroll_id.id,
                                                                                                        config=config,
                                                                                                        payroll_date=afkoop.date_afkoop)

                if not last_konjungtur_gaji:
                    raise ValidationError("Konjungtur belum dibuat. Anda tidak bisa melanjutkan aksi ini.")

                afkoop.konjungtur_gaji = last_konjungtur_gaji.value
                gaji_konjungtur = employee.get_gaji_konjungtur(last_konjungtur_gaji=last_konjungtur_gaji)
                afkoop.employee_gapok_total = gaji_konjungtur.get('gapok_total')
            else:
                afkoop.employee_gapok_total = afkoop.employee_gaji_pokok

            afkoop.total = afkoop.employee_gapok_total + afkoop.employee_tunjangan_rumah + \
                           afkoop.employee_tunjangan_jabatan + afkoop.employee_tunjangan_khusus + \
                           afkoop.employee_tunjangan_representasi
            afkoop.total_multiply = afkoop.total * int(afkoop.jumlah)

    def formatting_currency(self, value):
        """To convert currency format from float to Indonesian currency.

        Arguments:
            value {Float} -- Value which want to change.

        Returns:
            String -- Value string formatted.
        """
        return format_local_currency(value)

    def get_date_approve(self):
        """To convert `date_approve` from datetime to date.

        Returns:
            String -- String of `date_approve`.
        """
        return datetime_to_local_date(self.date_approve)
