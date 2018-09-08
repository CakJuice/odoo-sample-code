# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from ..helpers import datetime_to_local_date, format_local_currency


class KaHrPayrollTunjanganHolidays(models.Model):
    """Data of tunjangan_cuti. Generates automatically with yearly_holidays or big_holidays.

    _name = 'ka_hr_payroll.tunjangan.holidays'
    """

    _name = 'ka_hr_payroll.tunjangan.holidays'
    _order = 'date_tunjangan desc'
    _inherit = 'mail.thread'

    name = fields.Char(string="Nama", size=255)
    date_tunjangan = fields.Date(string="Tanggal Tunjangan", required=True, default=fields.Date.today,
                                 readonly=True, states={'draft': [('readonly', False)]})
    holiday_id = fields.Many2one('hr.holidays', string="Ref. Cuti", readonly=True, ondelete='cascade')
    holiday_employee_id = fields.Many2one('hr.employee', string="Karyawan", readonly=True)
    employee_gaji_pokok = fields.Float(string="Gaji Pokok", readonly=True, states={'draft': [('readonly', False)]})
    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", readonly=True, states={'draft': [('readonly', False)]})
    employee_tunjangan_rumah = fields.Float(string="Tunj. Rumah", readonly=True,
                                            states={'draft': [('readonly', False)]})
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", readonly=True,
                                          states={'draft': [('readonly', False)]})
    employee_tunjangan_jabatan = fields.Float(string="Tunj. Jabatan", readonly=True,
                                              states={'draft': [('readonly', False)]})
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", readonly=True, states={'draft': [('readonly', False)]})
    employee_tunjangan_khusus = fields.Float(string="Tunj. Khusus", readonly=True,
                                             states={'draft': [('readonly', False)]})
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", readonly=True,
                                               states={'draft': [('readonly', False)]})
    employee_tunjangan_representasi = fields.Float(string="Tunjangan Representasi", readonly=True,
                                                   states={'draft': [('readonly', False)]})
    konjungtur_gaji = fields.Float(string="Konjungtur Gaji (%)", readonly=True, states={'draft': [('readonly', False)]})
    is_multiply_konjungtur = fields.Boolean(string="Dikalikan Konjungtur", readonly=True,
                                            states={'draft': [('readonly', False)]})
    multiply_value = fields.Float(string="Nilai Pengali", digits=(5, 2), default=1.00, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  help="Nilai pengali sesuai dengan yang ada pada setting penggajian")
    employee_gapok_total = fields.Float(string="Gaji Pokok Total", compute='_compute_gapok', store=True)
    total = fields.Float(string="Total", compute='_compute_total', store=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('approved', "Disetujui"),
        ('canceled', "Dibatalkan"),
    ], string="Status", required=True, default='draft', track_visibility='onchange')
    date_approve = fields.Datetime(string="Tanggal Disetujui", required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}, default=fields.Datetime.now)
    notes = fields.Text(string="Catatan Persetujuan")
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", readonly=True)
    rapel_ref_ids = fields.One2many('ka_hr_payroll.payroll.tunjangan.holidays.rapel',
                                    'tunjangan_holidays_rapel_ref_id', string="Ref. Pembayar Rapel", readonly=True)

    hr_officer_notif = fields.Many2one('hr.employee', related='company_payroll_id.hr_notif_payroll')

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
        record = super(KaHrPayrollTunjanganHolidays, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_obj = datetime.strptime(record.date_tunjangan, DATE_FORMAT)
            date_str = date_obj.strftime('%d-%m-%Y')
            record.name = "{0} Tunjangan Cuti. Periode: {1}".format(record.holiday_employee_id.name, date_str)
            # send email to officer
            if record.hr_officer_notif:
                template = self.env.ref('ka_hr_payroll.template_mail_tunjangan_holidays')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
        return record

    @api.onchange('holiday_id')
    def _onchange_holiday(self):
        config = self.env['ka_hr_payroll.config'].default_config()
        employee = self.holiday_employee_id
        self.employee_gaji_pokok = employee.gaji_pokok

        self.is_tunjangan_rumah = employee.payroll_company_id.cuti_tunjangan_rumah
        if self.is_tunjangan_rumah:
            self.employee_tunjangan_rumah = employee.tunjangan_rumah
        else:
            self.employee_tunjangan_rumah = 0

        self.is_tunjangan_jabatan = employee.payroll_company_id.cuti_tunjangan_jabatan
        if self.is_tunjangan_jabatan:
            self.employee_tunjangan_jabatan = employee.tunjangan_jabatan
        else:
            self.employee_tunjangan_jabatan = 0

        self.is_tunjangan_khusus = employee.payroll_company_id.cuti_tunjangan_khusus
        if self.is_tunjangan_khusus:
            self.employee_tunjangan_khusus = employee.tunjangan_khusus
        else:
            self.employee_tunjangan_khusus = 0

        self.is_tunjangan_representasi = employee.payroll_company_id.cuti_tunjangan_representasi
        if self.is_tunjangan_representasi:
            self.employee_tunjangan_representasi = employee.tunjangan_representasi
        else:
            self.employee_tunjangan_representasi = 0

        self.multiply_value = employee.status_id.cuti_multiply

        self.is_multiply_konjungtur = employee.status_id.is_multiply_konjungtur

        if self.is_multiply_konjungtur:
            last_konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                    self.company_payroll_id.id,
                                                                                                    config=config,
                                                                                                    payroll_date=self.date_tunjangan)

            if not last_konjungtur_gaji:
                raise ValidationError("Konjungtur belum dibuat. Anda tidak bisa melanjutkan aksi ini.")

            self.konjungtur_gaji = last_konjungtur_gaji.value

    @api.depends('is_multiply_konjungtur', 'konjungtur_gaji', 'employee_gaji_pokok')
    def _compute_gapok(self):
        for tunjangan in self:
            if tunjangan.is_multiply_konjungtur:
                tunjangan.employee_gapok_total = tunjangan.employee_gaji_pokok * tunjangan.konjungtur_gaji / 100
            else:
                tunjangan.employee_gapok_total = tunjangan.employee_gaji_pokok

    @api.depends('employee_gapok_total', 'employee_tunjangan_rumah', 'employee_tunjangan_jabatan',
                 'employee_tunjangan_khusus', 'employee_tunjangan_representasi', 'multiply_value')
    def _compute_total(self):
        for tunjangan in self:
            tunjangan.total = (tunjangan.employee_gapok_total + tunjangan.employee_tunjangan_rumah + \
                               tunjangan.employee_tunjangan_jabatan + tunjangan.employee_tunjangan_khusus + \
                               tunjangan.employee_tunjangan_representasi) * tunjangan.multiply_value

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
        """Set `state='draft'`.
        """
        self.state = 'draft'

    def action_approve(self):
        """Set `state='approved'`.
        """
        if not self.date_approve:
            self.date_approve = fields.Datetime.now()
        self.state = 'approved'

    def action_cancel(self):
        """Set `state='canceled'`.
        """
        self.state = 'canceled'
