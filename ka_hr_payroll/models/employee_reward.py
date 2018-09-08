# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from __future__ import division

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from ..helpers import format_local_currency, datetime_to_local_date


class KaHrPayrollEmployeeReward(models.Model):
    """Data reward employee

    _name = 'ka_hr_payroll.employee.reward'
    """

    _name = 'ka_hr_payroll.employee.reward'
    _order = 'date_start desc'
    _inherit = 'mail.thread'

    REWARD_TYPE_NAME = [
        ('1', "Penghargaan Masa Dinas"),
        ('2', "Penghargaan Pisah Pensiun")
    ]

    name = fields.Char(string="Nama", size=255)
    date_start = fields.Date(string="Tanggal", required=True, default=fields.Date.today,
                             states={'approved': [('readonly', True)], 'canceled': [('readonly', True)]})
    employee_id = fields.Many2one('hr.employee', string="Karyawan", required=True,
                                  states={'approved': [('readonly', True)], 'canceled': [('readonly', True)]})
    reward_id = fields.Many2one('ka_hr_payroll.reward', string="Jenis Penghargaan", required=True,
                                states={'approved': [('readonly', True)], 'canceled': [('readonly', True)]})
    reward_type = fields.Selection(REWARD_TYPE_NAME, string="Tipe",
                                   states={'approved': [('readonly', True)], 'canceled': [('readonly', True)]})
    employee_gaji_pokok = fields.Float(string="Gaji Pokok", required=True)
    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah")
    employee_tunjangan_rumah = fields.Float(string="Tunj. Rumah", required=True)
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan")
    employee_tunjangan_jabatan = fields.Float(string="Tunj. Jabatan", required=True)
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus")
    employee_tunjangan_khusus = fields.Float(string="Tunj. Khusus", required=True)
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi")
    employee_tunjangan_representasi = fields.Float(string="Tunj.n Representasi", required=True)
    konjungtur_gaji = fields.Float(string="Konjungtur Gaji (%)", required=True)
    is_multiply_konjungtur = fields.Boolean(string="Dikalikan Konjungtur")
    multiply_value = fields.Float(string="Nilai Pengali", required=True)
    employee_gapok_total = fields.Float(string="Gaji Pokok Total", required=True)
    total_penerimaan = fields.Float(string="Total Penerimaan", required=True)
    total = fields.Float(string="Total", required=True)
    grand_total = fields.Float(string="Total Dibayar", compute='_compute_grand_total', store=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('approved', "Disetujui"),
        ('canceled', "Dibatalkan"),
    ], string="Status", required=True, default='draft', track_visibility='onchange')
    date_approve = fields.Datetime(string="Tanggal Disetujui", readonly=True,
                                   states={'draft': [('readonly', False)], 'processed': [('readonly', False)]})
    notes = fields.Text(string="Catatan Persetujuan")
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", compute='_compute_total',
                                         store=True)
    rapel_ref_ids = fields.One2many('ka_hr_payroll.payroll.employee.reward.rapel', 'employee_reward_rapel_ref_id',
                                    string="Ref. Pembayar Rapel", readonly=True)
    child_ids = fields.One2many('ka_hr_payroll.employee.reward.child', 'parent_id', string="Penghargaan Lain-Lain")

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
        record = super(KaHrPayrollEmployeeReward, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            record.name = "{0}. {1}".format(record.employee_id.name, record.reward_id.name)
        if not 'company_payroll_id' in vals or not vals.get('company_payroll_id'):
            record.company_payroll_id = record.employee_id.company_payroll_id
        return record

    @api.onchange('employee_id', 'reward_id')
    def _onchange_employee_reward(self):
        config = self.env['ka_hr_payroll.config'].default_config()

        employee = self.employee_id
        self.company_payroll_id = employee.company_payroll_id
        self.employee_gaji_pokok = employee.gaji_pokok

        self.is_tunjangan_rumah = self.reward_id.is_tunjangan_rumah
        if self.is_tunjangan_rumah:
            self.employee_tunjangan_rumah = employee.tunjangan_rumah
        else:
            self.employee_tunjangan_rumah = 0

        self.is_tunjangan_jabatan = self.reward_id.is_tunjangan_jabatan
        if self.is_tunjangan_jabatan:
            self.employee_tunjangan_jabatan = employee.tunjangan_jabatan
        else:
            self.employee_tunjangan_jabatan = 0

        self.is_tunjangan_khusus = self.reward_id.is_tunjangan_khusus
        if self.is_tunjangan_khusus:
            self.employee_tunjangan_khusus = employee.tunjangan_khusus
        else:
            self.employee_tunjangan_khusus = 0

        self.is_tunjangan_representasi = self.reward_id.is_tunjangan_representasi
        if self.is_tunjangan_representasi:
            self.employee_tunjangan_representasi = employee.tunjangan_representasi
        else:
            self.employee_tunjangan_representasi = 0

        self.multiply_value = self.reward_id.multiply_value

        self.is_multiply_konjungtur = employee.status_id.is_multiply_konjungtur
        if self.is_multiply_konjungtur:
            last_konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                    self.company_payroll_id.id,
                                                                                                    config=config,
                                                                                                    payroll_date=self.date_start)

            if not last_konjungtur_gaji:
                raise ValidationError("Konjungtur belum dibuat. Anda tidak bisa melanjutkan aksi ini.")

            self.konjungtur_gaji = last_konjungtur_gaji.value
            gaji_konjungtur = employee.get_gaji_konjungtur(last_konjungtur_gaji=last_konjungtur_gaji)
            self.employee_gapok_total = gaji_konjungtur.get('gapok_total')
        else:
            self.employee_gapok_total = self.employee_gaji_pokok

        self.total_penerimaan = self.employee_gapok_total + self.employee_tunjangan_rumah + \
                                self.employee_tunjangan_jabatan + self.employee_tunjangan_khusus + \
                                self.employee_tunjangan_representasi

        self.total = round(self.total_penerimaan * self.multiply_value)

    @api.depends('total', 'child_ids')
    def _compute_grand_total(self):
        for reward in self:
            reward.grand_total = reward.total + sum([child.total for child in reward.child_ids])

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

    def action_draft(self):
        """Set state to `draft`.
        """
        self.state = 'draft'

    def action_process(self):
        """Set state to `processed`.
        """
        self.state = 'processed'

    def action_approve(self):
        """Set state to `approved`.
        """
        if not self.date_approve:
            self.date_approve = fields.Date.today()
        self.state = 'approved'

    def action_cancel(self):
        """Set `state='canceled'`.
        """
        self.state = 'canceled'


class KaHrPayrollEmployeeRewardOther(models.Model):
    _name = 'ka_hr_payroll.employee.reward.child'

    parent_id = fields.Many2one('ka_hr_payroll.employee.reward', string="Parent Reward", required=True)
    reward_type = fields.Selection([
        ('1', "Afkoop Cuti Panjang Berimbang"),
        ('2', "Afkoop Cuti Tahunan Berimbang"),
        ('3', "Sisa Cuti Tahunan & Cuti Besar"),
    ], string="Jenis", required=True)
    description = fields.Char(string="Deskripsi", size=255)
    proportion_value = fields.Char(string="Nilai Proporsi", required=True, size=6)
    total_penerimaan = fields.Float(string="Total Penerimaan", related='parent_id.total_penerimaan', store=True,
                                    required=True)
    total = fields.Float(string="Total", compute='_compute_total', store=True)

    @api.depends('proportion_value', 'total_penerimaan')
    def _compute_total(self):
        for child in self:
            if child.proportion_value and child.total_penerimaan:
                try:
                    proportion = eval(child.proportion_value)
                    child.total = round(proportion * child.total_penerimaan)
                except Exception:
                    raise ValidationError("Nilai proporsi salah. Nilai proporsi harus bentuk pecahan.")
