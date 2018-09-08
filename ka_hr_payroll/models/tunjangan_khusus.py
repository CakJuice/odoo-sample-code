# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from ..helpers import get_utc_timezone, check_rapel_status


class KaHrPayrollTunjanganKhusus(models.Model):
    """Data of combine special allowance (Tunjangan Khusus) of employee.

    _name = 'ka_hr_payroll.tunjangan.khusus.combine'
    """

    _name = 'ka_hr_payroll.tunjangan.khusus.combine'
    _description = "Data kombinasi tunjangan khusus karyawan"
    _order = 'name asc'
    _inherit = 'mail.thread'

    name = fields.Char(string="Nama", size=255)
    jabatan_id = fields.Many2one('hr.jabatan', string="Jabatan", required=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    golongan_id = fields.Many2one('hr.golongan', string="Golongan", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('locked', "Dikunci"),
    ], string="Status", default='draft', required=True, track_visibility='onchange')
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         default=lambda self: self.env.user.company_id,
                                         states={'draft': [('readonly', False)]})
    pangkat_ids = fields.Many2many('hr.pangkat', 'pangkat_tunjangan_khusus', 'tunjangan_id',
                                   'pangkat_id', string="Pangkat", readonly=True,
                                   states={'draft': [('readonly', False)]})

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
        tunjangan = super(KaHrPayrollTunjanganKhusus, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            tunjangan.name = "Kombinasi Tunj. Khusus {0} Golongan: {1}".format(tunjangan.jabatan_id.name,
                                                                               tunjangan.golongan_id.name)
        return tunjangan

    @api.multi
    def action_draft(self):
        """Set state to `draft`.

        Decorators:
            api.multi
        """
        self.state = 'draft'

    @api.multi
    def action_lock(self):
        """Set state to `lock`.

        Decorators:
            api.multi
        """
        self.state = 'locked'

    def get_combine(self, jabatan_id, golongan_id, pangkat_id, company_payroll_id):
        """Get data combine of employee.

        Arguments:
            jabatan_id {Int} -- ID of `hr.jabatan`.
            golongan_id {Int} -- ID of `hr.golongan`.
            pangkat_id {Int} -- ID of `hr.pangkat`.
            company_payroll_id {Int} -- ID of `res.company`.

        Returns:
            Recordset or None -- Result of query with limit `1` or None.
        """
        tunjangans = self.search([
            ('jabatan_id', '=', jabatan_id),
            ('golongan_id', '=', golongan_id),
            ('state', '=', 'locked'),
            ('company_payroll_id', '=', company_payroll_id),
        ])

        for tunjangan in tunjangans:
            if pangkat_id in tunjangan.pangkat_ids.ids:
                return tunjangan

        return None

    def generate_dummy(self):
        data_combine = [
            ('08', 'VII', '1', ['08']),
            ('10', 'VII', '1', ['08']),
            ('09', 'VII', '1', ['08']),
            ('11', 'VI', '1', ['09']),
            ('13', 'VI', '1', ['09']),
            ('14', 'VI', '1', ['09']),
            ('14', 'V', '1', ['09', '15', '20', '25', '30']),
            ('15', 'V', '1', ['10', '15', '20', '25', '30']),
            ('15', 'V', '1', ['11', '16', '21', '26', '31']),
            ('15', 'IV', '1', ['11', '16', '21', '26', '31']),
            ('15', 'IV', '1', ['12', '17', '22', '27', '32']),
            ('15', 'III', '1', ['12', '17', '22', '27', '32']),
            ('16', 'III', '1', ['12', '17', '22', '27', '32']),
            ('16', 'II', '1', ['13', '18', '28', '33']),
            ('16', 'I', '1', ['14', '19', '29', '34']),
        ]

        idx = 1
        for jabatan_code, golongan_code, company_payroll_code, pangkat_codes in data_combine:
            golongan = self.env['hr.golongan'].search([('name', '=', golongan_code)], limit=1)
            jabatan = self.env['hr.jabatan'].search([('code', '=', jabatan_code)], limit=1)
            company = self.env['res.company'].search([('code', '=', company_payroll_code)], limit=1)
            data = {
                'jabatan_id': jabatan.id,
                'golongan_id': golongan.id,
                'company_payroll_id': company.id,
            }
            combine = self.create(data)
            pangkats = self.env['hr.pangkat'].search([('code', 'in', pangkat_codes)])
            combine.pangkat_ids = pangkats
            idx_str = '0{0}'.format(idx) if idx < 10 else str(idx)
            name = combine.name
            combine.name = "No. {0}: {1}".format(idx_str, name)
            combine.action_lock()
            idx += 1


class KaHrPayrollTunjanganKhususPeriod(models.Model):
    """Data periode of special allowance (Periode Tunjangan Khusus) of employee.

    _name = 'ka_hr_payroll.tunjangan.khusus.period'
    """

    _name = 'ka_hr_payroll.tunjangan.khusus.period'
    _order = 'date_start desc'

    name = fields.Char(string="Nama Periode", size=255)
    date_start = fields.Date(string="Tanggal Mulai", required=True, default=fields.Date.today,
                             readonly=True, states={'draft': [('readonly', False)]})
    status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True, readonly=True,
                                states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('rapel', "Rapel"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan"),
    ], string="Status", default='draft', required=True)
    date_approve = fields.Datetime(string="Tanggal Disetujui", readonly=True,
                                   states={'processed': [('readonly', False)]})
    date_done = fields.Datetime(string="Tanggal Berlaku", readonly=True,
                                states={'processed': [('readonly', False)]})
    no_sk = fields.Char(string="Nomor SK", size=24)
    notes = fields.Text(string="Catatan Persetujuan")
    state_rapel = fields.Selection([
        ('0', "Tidak Ada Rapel"),
        ('1', "Rapel Belum Diproses"),
        ('2', "Rapel Sudah Diproses"),
    ], string="Status Rapel", default='0', readonly=True)
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.tunjangan.khusus.period', string="Referensi Rapel",
                               readonly=True)
    company_payroll_id = fields.Many2one('res.company', required=True, readonly=True,
                                         states={'draft': [('readonly', False)]}, string="Lokasi Penggajian",
                                         default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('ka_hr_payroll.tunjangan.khusus.period.lines', 'period_id',
                               string="Detail Tunjangan", readonly=True, states={'draft': [('readonly', False)]})

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
        period = super(KaHrPayrollTunjanganKhususPeriod, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_start_obj = datetime.strptime(period.date_start, DATE_FORMAT)
            date_start_str = date_start_obj.strftime('%d-%m-%Y')
            period.name = "Tunjangan Khusus Periode: {0}".format(date_start_str)
        return period

    @api.multi
    def action_draft(self):
        """Set state to `draft`.

        Decorators:
            api.multi
        """
        self.state = 'draft'

    @api.multi
    def action_process(self):
        """Set state to `processed`.

        Decorators:
            api.multi
        """
        if not self.line_ids or len(self.line_ids) <= 0:
            raise ValidationError("Data detail tunjangan masih kosong!")
        self.state = 'processed'

    @api.multi
    def action_approve(self):
        """Check rapel and set state to `rapel` or `done`.

        Decorators:
            api.multi
        """
        if not self.date_approve:
            self.date_approve = fields.Datetime.now()

        config = self.env['ka_hr_payroll.config'].default_config()
        if check_rapel_status(self, config):
            self.action_rapel()
        else:
            self.action_done()

    @api.multi
    def action_rapel(self):
        """Set `state` to `rapel` and `state_rapel` to `2`.

        Decorators:
            api.multi
        """
        self.state = 'rapel'
        self.state_rapel = '1'

    def get_last_period(self, status_id, company_payroll_id, config=None):
        """To get last period which `state = done`.

        Arguments:
            status_id {Int} -- ID of `hr.status`.
            company_payroll_id {Int} -- ID of `res.company`.
            config {Recordset} -- Result from `ka_hr_payroll.config` `default_config()`.

        Returns:
            Recordset -- Result of query with limit `1` and order by `date_start desc`.
        """
        if not config:
            config = self.env['ka_hr_payroll.config'].default_config()

        date_now = datetime.now().date()
        date_config = datetime.strptime("{0}-{1}-{2}".format(date_now.year, date_now.month, config.date_start),
                                        DATE_FORMAT)
        date_config_str = date_config.strftime(DATE_FORMAT)

        return self.search([
            ('date_start', '<=', fields.Date.today()),
            ('status_id', 'parent_of', status_id),
            ('state', '=', 'done'),
            ('state_rapel', '!=', '1'),
            ('date_done', '<', date_config_str),
            ('company_payroll_id', '=', company_payroll_id)
        ], limit=1, order='date_start desc')

    def generate_rapel(self):
        """To generate rapel, based on new period and last period of tunjangan khusus.

        Raises:
            ValidationError -- Raise when last period not found.
        """
        config = self.env['ka_hr_payroll.config'].default_config()
        last_period = self.get_last_period(self.status_id.id, self.company_payroll_id.id, config=config)
        if last_period:
            date_done = datetime.strptime(self.date_done, DATETIME_FORMAT)

            if date_done.day > config.date_end:
                date_pay = date_done + relativedelta(months=1)
            else:
                date_pay = date_done

            data_rapel = {
                'new_period_id': self.id,
                'old_period_id': last_period.id,
                'date_start': get_utc_timezone(self.date_start + ' 00:00:00'),
                'date_end': self.date_done,
                'year_pay': str(date_pay.year),
                'month_pay': date_pay.month,
                'status_id': self.status_id.id,
                'company_payroll_id': self.company_payroll_id.id,
            }

            rapel_period = self.env['ka_hr_payroll.rapel.tunjangan.khusus.period'].create(data_rapel)
            self.rapel_id = rapel_period

            for line in self.line_ids:
                line.generate_rapel(last_period.id, rapel_period.id)

            self.state_rapel = '2'
            self.env.user.notify_info("{0}, berhasil dibuat!".format(rapel_period.name))
        else:
            raise ValidationError(
                "Tunjangan khusus periode sebelumnya tidak ditemukan! Anda tidak bisa melanjutkan aksi ini.")

    @api.multi
    def action_done(self):
        """Generate rapel then set `state` to `done` and `date_done` to date now.

        Decorators:
            api.multi
        """
        if not self.date_done:
            self.date_done = fields.Datetime.now()
        if self.state_rapel == '1':
            self.generate_rapel()
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        """Set state to `canceled`.

        Decorators:
            api.multi
        """
        self.state = 'canceled'

    def generate_dummy(self):
        status = self.env['hr.status'].search([('code', '=', '02')], limit=1)
        company = self.env['res.company'].search([('code', '=', '1')], limit=1)
        data = {
            'date_start': '2017-01-01',
            'status_id': status.id,
            'company_payroll_id': company.id,
            'date_approve': '2017-01-03 00:00:00',
            'date_done': '2017-01-03 00:00:00',
        }
        tunjangan = self.create(data)
        combines = self.env['ka_hr_payroll.tunjangan.khusus.combine'].search([], order='id asc')
        value = [8850000, 7750000, 7000000, 6650000, 6100000, 5550000, 5200000, 4450000, 4000000, 3700000,
                 3350000, 3100000, 2500000, 2000000, 1600000]
        idx = 0
        for combine in combines:
            self.env['ka_hr_payroll.tunjangan.khusus.period.lines'].create({
                'period_id': tunjangan.id,
                'combine_id': combine.id,
                'value': value[idx]
            })
            idx += 1
        tunjangan.action_process()
        tunjangan.action_approve()


class KaHrPayrollTunjanganKhususPeriodLines(models.Model):
    """Data lines of tunjangan khusus period.

    _name = 'ka_hr_payroll.tunjangan.khusus.period.lines'
    """

    _name = 'ka_hr_payroll.tunjangan.khusus.period.lines'

    name = fields.Char(string="Nama", size=255)
    period_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.period', string="Periode Tunj. Khusus",
                                required=True, ondelete='cascade')
    combine_id = fields.Many2one('ka_hr_payroll.tunjangan.khusus.combine', string="Penerima",
                                 required=True, domain=[('state', '=', 'locked')])
    value = fields.Float(string="Nilai Tunj.", required=True)

    _sql_constraints = [
        ('tunjangan_khusus_period_lines_unique', 'UNIQUE(period_id, combine_id)', "Data penerima sudah ada!")
    ]

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
        lines = super(KaHrPayrollTunjanganKhususPeriodLines, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_obj = datetime.strptime(lines.period_id.date_start, DATE_FORMAT)
            date_str = date_obj.strftime('%d-%m-%Y')
            lines.name = "Detail {0}. Periode: {1}".format(lines.combine_id.name, date_str)
        return lines

    def get_last_lines(self, period_id, combine_id):
        """To get last lines before this record.

        Arguments:
            period_id {Int} -- ID of this model parent from `ka_hr_payroll.tunjangan.khusus.period`.
            combine_id {Int} -- ID of `ka_hr_payroll.tunjangan.khusus.combine`.

        Returns:
            Recordset -- Result of query with `limit=1`.
        """
        return self.search([
            ('period_id', '=', period_id),
            ('combine_id', '=', combine_id),
        ], limit=1)

    def generate_rapel(self, last_period_id, rapel_period_id):
        """To generate rapel tunjangan khusus lines.

        Arguments:
            last_period_id {Int} -- ID this model parent from `ka_hr_payroll.tunjangan.khusus.period`.
            rapel_period_id {Int} -- ID of `ka_hr_payroll.rapel.tunjangan.khusus.period` which generated from this parent.
        """
        last_lines = self.get_last_lines(last_period_id, self.combine_id.id)
        data_rapel_lines = {
            'rapel_period_id': rapel_period_id,
            'new_period_lines_id': self.id,
            'new_value': self.value,
            'combine_id': self.combine_id.id,
        }

        if last_lines:
            data_rapel_lines['old_period_lines_id'] = last_lines.id
            data_rapel_lines['old_value'] = last_lines.value

        self.env['ka_hr_payroll.rapel.tunjangan.khusus.period.lines'].create(data_rapel_lines)


class KaHrPayrollPangkat(models.Model):
    """Master data of employee job rank (pangkat).

    _inherit = 'hr.pangkat'
    """

    _inherit = 'hr.pangkat'

    tunjangan_khusus_combine_ids = fields.Many2many('ka_hr_payroll.tunjangan.khusus.combine',
                                                    'pangkat_tunjangan_khusus',
                                                    'pangkat_id', 'tunjangan_combine_id',
                                                    string="Kombinasi Tunjangan Khusus")
