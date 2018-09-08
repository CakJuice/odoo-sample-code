# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from __future__ import division

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError

from ..helpers import MONTH_LIST, format_local_currency, date_to_local_date


class KaHrPayrollPayroll(models.Model):
    """Manage payroll data periodically.

    _name = 'ka_hr_payroll.payroll'
    """

    _name = 'ka_hr_payroll.payroll'
    _order = 'date_payroll desc'
    _inherit = 'mail.thread'

    PAYROLL_TYPE = [
        ('1', "Gaji Bulanan"),
        ('2', "Tunjangan Hari Raya"),
    ]

    name = fields.Char(string="Nama Penggajian", size=255)
    year_period = fields.Char(string="Tahun Periode", size=4, required=True, readonly=True,
                              default=str(datetime.now().year), states={'draft': [('readonly', False)]})
    month_period = fields.Selection(MONTH_LIST, string="Bulan Periode", required=True, readonly=True,
                                    default=datetime.now().month, states={'draft': [('readonly', False)]})
    date_payroll = fields.Date(string="Tanggal Penggajian", required=True, readonly=True,
                               default=fields.Date.today, states={'draft': [('readonly', False)]})
    employee_status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True,
                                         readonly=True, states={'draft': [('readonly', False)]},
                                         domain=[('parent_id', '=', None)])
    payroll_type = fields.Selection(PAYROLL_TYPE, string="Jenis Penggajian", default='1', required=True,
                                    readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('done', "Selesai"),
    ], string="Status", default='draft', required=True, track_visibility='onchange')
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         default=lambda self: self.env.user.company_id,
                                         states={'draft': [('readonly', False)]})
    payroll_employee_ids = fields.One2many('ka_hr_payroll.payroll.employee', 'payroll_id',
                                           string="Penggajian Karyawan", readonly=True)

    _sql_constraints = [
        ('employee_payroll_unique',
         'UNIQUE(year_period, month_period, employee_status_id, payroll_type, company_payroll_id)',
         "Periode penggajian sudah pernah diproses! Anda tidak diperkenankan melakukan aksi ini.")
    ]

    @api.constrains('year_period')
    def _check_year(self):
        if not self.year_period.isnumeric():
            raise ValidationError("Tahun harus berupa angka.")

    def _get_type_name(self, key):
        """To get type name of `payroll_type` value.

        Arguments:
            key {String} -- `payroll_type` value.

        Returns:
            String -- Result of `scale_type` value check.
        """
        for _type in self.PAYROLL_TYPE:
            if _type[0] == key:
                return _type[1]
        return ''

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
        payroll = super(KaHrPayrollPayroll, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            month_name = MONTH_LIST[payroll.month_period - 1][1]
            payroll.name = "{0} {1} {2}. Periode: {3} {4}".format(self._get_type_name(payroll.payroll_type),
                                                                  payroll.employee_status_id.name,
                                                                  payroll.company_payroll_id.name, month_name,
                                                                  payroll.year_period)
        return payroll

    @api.multi
    def action_process(self):
        """Change `state = processed`, then process payroll.
        """
        self.state = 'processed'
        self._process_payroll()

    @api.multi
    def action_done(self):
        """Change `state = done`, then process payroll.
        """
        self.state = 'done'

    @api.multi
    def action_back_process(self):
        """Back `state = processed`.
        """
        self.state = 'processed'

    def _get_rapel_list(self, rapel):
        return {
            'rapel': rapel,
            'date_start': rapel.date_start,
            'date_end': rapel.date_end,
        }

    def get_company_rapel_list(self):
        """Generate rapel list based on company.

        Returns:
            List -- List of rapel.
        """
        rapel_company = []

        rapel_scale_gp = self.env['ka_hr_payroll.rapel.scale.period'].get_approved_rapel_scale_period('gp',
                                                                                                      self.year_period,
                                                                                                      self.month_period,
                                                                                                      self.employee_status_id.id,
                                                                                                      self.company_payroll_id.id)
        if rapel_scale_gp:
            rapel_company.append(self._get_rapel_list(rapel_scale_gp))

        rapel_scale_tr = self.env['ka_hr_payroll.rapel.scale.period'].get_approved_rapel_scale_period('tr',
                                                                                                      self.year_period,
                                                                                                      self.month_period,
                                                                                                      self.employee_status_id.id,
                                                                                                      self.company_payroll_id.id)
        if rapel_scale_tr:
            rapel_company.append(self._get_rapel_list(rapel_scale_tr))

        rapel_scale_tj = self.env['ka_hr_payroll.rapel.scale.period'].get_approved_rapel_scale_period('tj',
                                                                                                      self.year_period,
                                                                                                      self.month_period,
                                                                                                      self.employee_status_id.id,
                                                                                                      self.company_payroll_id.id)
        if rapel_scale_tj:
            rapel_company.append(self._get_rapel_list(rapel_scale_tj))

        rapel_tunjangan_khusus = self.env['ka_hr_payroll.rapel.tunjangan.khusus.period'].get_approved_rapel(
            self.year_period, self.month_period, self.employee_status_id.id, self.company_payroll_id.id)
        if rapel_tunjangan_khusus:
            rapel_company.append((rapel_tunjangan_khusus.date_start, rapel_tunjangan_khusus.date_end))

        rapel_tunjangan_representasi = self.env['ka_hr_payroll.rapel.tunjangan.representasi'].get_approved_rapel(
            self.year_period, self.month_period, self.employee_status_id.id, self.company_payroll_id.id)
        if rapel_tunjangan_representasi:
            rapel_company.append(self._get_rapel_list(rapel_tunjangan_representasi))

        rapel_company_konjungtur = self.env['ka_hr_payroll.rapel.company.konjungtur'].get_approved_rapel(
            self.year_period, self.month_period, self.company_payroll_id.id)
        if rapel_company_konjungtur:
            rapel_company.append(self._get_rapel_list(rapel_company_konjungtur))

        rapel_company_default = self.env['ka_hr_payroll.rapel.company.default'].get_approved_rapel(
            self.year_period, self.month_period, self.employee_status_id.id, self.company_payroll_id.id)
        if rapel_company_default:
            rapel_company.append(self._get_rapel_list(rapel_company_default))

        return rapel_company

    def _process_payroll(self):
        """To process payroll each employee.
        """
        employees = self.env['hr.employee'].search([
            ('pensiun', '=', False),
            ('status_id', 'child_of', self.employee_status_id.id),
            ('company_payroll_id', '=', self.company_payroll_id.id)
        ])

        config = self.env['ka_hr_payroll.config'].default_config()
        last_konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                self.company_payroll_id.id,
                                                                                                config=config,
                                                                                                payroll_date=self.date_payroll)
        last_konjungtur_dapen = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('2',
                                                                                                 self.company_payroll_id.id,
                                                                                                 config=config,
                                                                                                 payroll_date=self.date_payroll)

        if not last_konjungtur_gaji:
            raise ValidationError("Konjungtur Gaji belum diinput. Anda tidak bisa melanjutkan proses ini.")
        if not last_konjungtur_dapen:
            raise ValidationError("Konjungtur Dapen belum diinput. Anda tidak bisa melanjutkan proses ini.")

        company_rapel = None
        if self.payroll_type == '1':
            company_rapel = self.get_company_rapel_list()

        data_payroll = {
            'payroll': self,
            'last_konjungtur_gaji': last_konjungtur_gaji,
            'last_konjungtur_dapen': last_konjungtur_dapen,
            'company_rapel': company_rapel,
        }

        for employee in employees:
            if self.payroll_type == '2' and not employee.status_id.is_thr:
                continue

            employee.generate_payroll(data_payroll, config=config)

        if self.payroll_type == '1' and company_rapel:
            for cr in company_rapel:
                rapel = cr.get('rapel')
                if rapel:
                    rapel.action_done(self)

        info = "Data {0} berhasil diproses!".format(self._get_type_name(self.payroll_type))
        self.env.user.notify_info(info)

    @api.multi
    def action_view_payroll_employee(self):
        """To open `ka_hr_payroll.payroll.employee`.

        Returns:
            Dict -- Action result.
        """
        action = self.env.ref('ka_hr_payroll.action_payroll_employee')
        result = action.read()[0]
        result['domain'] = [('payroll_id', '=', self.id)]
        result['context'] = {
            'default_payroll_id': self.id
        }
        return result

    # def get_potongan(self):
    #     return self.env['ka_hr_payroll.potongan'].search([
    #         ('is_mandatory', '=', True)
    #     ], order='id asc')


class KaHrPayrollPayrollEmployee(models.Model):
    """Lines of `ka_hr_payroll.payroll`.
    List of all employee which get paid related on `ka_hr_payroll.payroll`.

    _name = 'ka_hr_payroll.payroll.employee'
    """

    _name = 'ka_hr_payroll.payroll.employee'
    _order = 'name asc'

    name = fields.Char(string="Nama Penggajian Karyawan", size=255)
    payroll_id = fields.Many2one('ka_hr_payroll.payroll', string="Ref. Penggajian Karyawan", required=True,
                                 ondelete='cascade')
    payroll_date = fields.Date(string="Tanggal", related='payroll_id.date_payroll', store=True)
    payroll_type = fields.Selection(KaHrPayrollPayroll.PAYROLL_TYPE, string="Jenis Penggajian",
                                    related='payroll_id.payroll_type', store=True)
    payroll_year_period = fields.Char(string="Tahun Periode", related='payroll_id.year_period', size=4)
    payroll_month_period = fields.Selection(MONTH_LIST, related='payroll_id.month_period', string="Bulan Periode")
    payroll_state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('done', "Selesai"),
    ], string="Status Penggajian", related='payroll_id.state')
    employee_id = fields.Many2one('hr.employee', string="Karyawan", required=True)
    employee_company_id = fields.Many2one('res.company', string="Unit/PG", related='employee_id.payroll_company_id',
                                          store=True)
    employee_status_id = fields.Many2one('hr.status', string="Status Karyawan", related='employee_id.payroll_status_id',
                                         store=True)
    konjungtur_gaji = fields.Float(string="Konj. Gaji (%)")
    konjungtur_dapen = fields.Float(string="Konj. Dapen (%)")
    is_multiply_konjungtur = fields.Boolean(string="Dikalikan Konjungtur")
    is_proportion = fields.Boolean(string="Dikalikan Proporsi")
    proportion_value = fields.Char(string="Nilai Proporsi", size=8, default='12/12',
                                   help="Nilai proporsional dalam tipe string, misal '1/12', '2/12', dst.")
    gaji_pokok = fields.Float(string="Gaji Pokok")
    gapok_total = fields.Float(string="Gaji Pokok Total", compute='_compute_total', store=True)
    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah")
    tunjangan_rumah = fields.Float(string="Tunj. Rumah")
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan")
    tunjangan_jabatan = fields.Float(string="Tunj. Jabatan")
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus")
    tunjangan_khusus = fields.Float(string="Tunj. Khusus")
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi")
    tunjangan_representasi = fields.Float(string="Tunj. Representasi")
    multiply_value = fields.Float(string="Nilai Pengali", digits=(5, 2), default=1.00)
    total_pre_rapel = fields.Float(string="Total Sebelum Rapel", compute='_compute_total', store=True)
    rapel = fields.Float(string="Rapel", default=0.0)
    total_penerimaan = fields.Float(string="Total Penerimaan", compute='_compute_total', store=True)
    total_potongan = fields.Float(string="Total Potongan", compute='_compute_total', store=True)
    total = fields.Float(string="Total", compute='_compute_total', store=True)
    grand_total = fields.Float(string="Grand Total", compute='_compute_total', store=True)
    notes = fields.Text(string="Catatan")
    potongan_line_ids = fields.One2many('ka_hr_payroll.payroll.employee.potongan.lines', 'payroll_employee_id',
                                        string="Detail Potongan")
    rapel_pay_ids = fields.One2many('ka_hr_payroll.payroll.employee.rapel', 'payroll_rapel_pay_id',
                                    string="Ref. Rapel Dibayar")
    rapel_ref_ids = fields.One2many('ka_hr_payroll.payroll.employee.rapel', 'payroll_rapel_ref_id',
                                    string="Ref. Pembayar Rapel")
    afkoop_ref_ids = fields.One2many('ka_hr_payroll.payroll.afkoop.rapel', 'payroll_rapel_pay_id',
                                     string="Ref. Rapel Afkoop Dibayar")
    tunjangan_holidays_ref_ids = fields.One2many('ka_hr_payroll.payroll.tunjangan.holidays.rapel',
                                                 'payroll_rapel_pay_id', string="Ref. Tunjangan Cuti Dibayar")
    employee_reward_ref_ids = fields.One2many('ka_hr_payroll.payroll.employee.reward.rapel',
                                              'payroll_rapel_pay_id', string="Ref. Penghargaan Dibayar")

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
        record = super(KaHrPayrollPayrollEmployee, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            record.name = "{0} - {1}".format(record.employee_id.name, record.payroll_id.name)
        return record

    @api.onchange('employee_id')
    def _onchange_employee(self):
        self.gaji_pokok = self.employee_id.gaji_pokok
        self.tunjangan_rumah = self.employee_id.tunjangan_rumah
        self.tunjangan_jabatan = self.employee_id.tunjangan_jabatan
        self.tunjangan_khusus = self.employee_id.tunjangan_khusus
        self.tunjangan_representasi = self.employee_id.tunjangan_representasi

        config = self.env['ka_hr_payroll.config'].default_config()
        company_payroll_id = self.employee_id.company_payroll_id
        self.konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                company_payroll_id.id,
                                                                                                config=config, payroll_date=self.payroll_date).value or 0.0
        self.konjungtur_dapen = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('2',
                                                                                                 company_payroll_id.id,
                                                                                                 config=config, payroll_date=self.payroll_date).value or 0.0

    def generate_total(self):
        self.total_pre_rapel = self.gapok_total

        if self.is_tunjangan_rumah:
            self.total_pre_rapel += self.tunjangan_rumah

        if self.is_tunjangan_jabatan:
            self.total_pre_rapel += self.tunjangan_jabatan

        if self.is_tunjangan_khusus:
            self.total_pre_rapel += self.tunjangan_khusus

        if self.is_tunjangan_representasi:
            self.total_pre_rapel += self.tunjangan_representasi

        self.total_penerimaan = (self.total_pre_rapel * self.multiply_value) + self.rapel

        self.total_potongan = 0
        for potongan in self.potongan_line_ids:
            self.total_potongan += potongan.value

        self.total = self.total_penerimaan - self.total_potongan
        self.grand_total = self.total
        if self.is_proportion:
            proportion = eval(self.proportion_value)
            self.grand_total = round(self.total * proportion)

    @api.depends('gaji_pokok', 'is_multiply_konjungtur', 'konjungtur_gaji', 'is_tunjangan_rumah',
                 'tunjangan_rumah', 'is_tunjangan_jabatan', 'tunjangan_jabatan', 'is_tunjangan_khusus',
                 'tunjangan_khusus', 'is_tunjangan_representasi', 'tunjangan_representasi', 'is_proportion',
                 'proportion_value', 'multiply_value', 'potongan_line_ids')
    def _compute_total(self):
        if self.proportion_value:
            try:
                eval(self.proportion_value)
            except Exception:
                raise ValidationError("Nilai proporsi salah. Nilai proporsi harus bentuk pecahan.")

        if self.is_multiply_konjungtur:
            self.gapok_total = self.gaji_pokok * self.konjungtur_gaji / 100.0
        else:
            self.gapok_total = self.gaji_pokok

        self.generate_total()

    def formatting_currency(self, value):
        """To convert currency format from float to Indonesian currency.

        Arguments:
            value {Float} -- Value which want to change.

        Returns:
            String -- Value string formatted.
        """
        return format_local_currency(value)

    def get_date_payroll(self):
        """To convert `date_approve` from datetime to date.

        Returns:
            String -- String of `date_approve`.
        """
        return date_to_local_date(self.payroll_date)


class KaHrPayrollPayrollEmployeeRapel(models.Model):
    _name = 'ka_hr_payroll.payroll.employee.rapel'

    payroll_rapel_pay_id = fields.Many2one('ka_hr_payroll.payroll.employee', string="Penggajian Pembayar Rapel",
                                           required=True, help="Ref. penggajian pembayar rapel.", ondelete='cascade')
    payroll_rapel_ref_id = fields.Many2one('ka_hr_payroll.payroll.employee', string="Penggajian Rapel Dibayar",
                                           required=True, help="Ref. penggajian rapel yang dibayar.")
    payroll_rapel_value = fields.Float(string="Nilai Rapel", required=True, help="Nilai rapel yang dibayar.")


class KaHrPayrollPayrollAfkoopRapel(models.Model):
    _name = 'ka_hr_payroll.payroll.afkoop.rapel'

    payroll_rapel_pay_id = fields.Many2one('ka_hr_payroll.payroll.employee', string="Penggajian Pembayar Rapel",
                                           required=True, help="Ref. penggajian pembayar rapel.", ondelete='cascade')
    afkoop_rapel_ref_id = fields.Many2one('ka_hr.holidays.afkoop', string="Afkoop Rapel Dibayar",
                                          required=True, help="Ref. afkoop rapel yang dibayar.")
    afkoop_rapel_value = fields.Float(string="Nilai Rapel", required=True, help="Nilai rapel yang dibayar.")


class KaHrPayrollPayrollTunjanganHolidaysRapel(models.Model):
    _name = 'ka_hr_payroll.payroll.tunjangan.holidays.rapel'

    payroll_rapel_pay_id = fields.Many2one('ka_hr_payroll.payroll.employee', string="Penggajian Pembayar Rapel",
                                           required=True, help="Ref. penggajian pembayar rapel.", ondelete='cascade')
    tunjangan_holidays_rapel_ref_id = fields.Many2one('ka_hr_payroll.tunjangan.holidays',
                                                      string="Tunjangan Cuti Rapel Dibayar", required=True,
                                                      help="Ref. tunjangan cuti yang dibayar")
    tunjangan_holidays_rapel_value = fields.Float(string="Nilai Rapel", required=True, help="Nilai rapel yang dibayar")


class KaHrPayrollPayrollEmployeeRewardRapel(models.Model):
    _name = 'ka_hr_payroll.payroll.employee.reward.rapel'

    payroll_rapel_pay_id = fields.Many2one('ka_hr_payroll.payroll.employee', string="Penggajian Pembayar Rapel",
                                           required=True, help="Ref. penggajian pembayar rapel.", ondelete='cascade')
    employee_reward_rapel_ref_id = fields.Many2one('ka_hr_payroll.employee.reward',
                                                   string="Penghargaan Rapel Dibayar", required=True,
                                                   help="Ref. penghargaan masa kerja yang dibayar")
    employee_reward_rapel_value = fields.Float(string="Nilai Rapel", required=True, help="Nilai rapel yang dibayar")


class KaHrPayrollPayrollEmployeePotonganLines(models.Model):
    """Lines of `ka_hr_payroll.payroll.employee`.
    List of all deduction (potongan) which related on `ka_hr_payroll.payroll.employee`.

    _name = 'ka_hr_payroll.payroll.employee.potongan.lines'
    """

    _name = 'ka_hr_payroll.payroll.employee.potongan.lines'

    payroll_employee_id = fields.Many2one('ka_hr_payroll.payroll.employee', string="Penggajian Karyawan",
                                          required=True, ondelete='cascade', readonly=True)
    potongan_id = fields.Many2one('ka_hr_payroll.potongan', string="Nama Potongan", required=True)
    value = fields.Float(string="Nilai Potongan", required=True)
