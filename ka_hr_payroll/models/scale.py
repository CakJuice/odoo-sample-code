# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from __future__ import division

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from ..helpers import get_utc_timezone, check_rapel_status


class KaHrPayrollScalePeriod(models.Model):
    """Data of scale period. It can be base salary scale, or allowance scale.

    _name = 'ka_hr_payroll.scale.period'
    """

    _name = 'ka_hr_payroll.scale.period'
    _description = "Periode skala penggajian karyawan"
    _order = 'date_start desc'
    _inherit = 'mail.thread'

    SCALE_TYPE_NAME = [
        ('gp', "Gaji Pokok"),
        ('tr', "Tunj. Rumah"),
        ('tj', "Tunj. Jabatan"),
    ]

    name = fields.Char(string="Nama Periode Skala", size=255)
    date_start = fields.Date(string="Tanggal Mulai", required=True, readonly=True, default=fields.Date.today,
                             states={'draft': [('readonly', False)]})
    status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True, readonly=True,
                                states={'draft': [('readonly', False)]})
    scale_type = fields.Selection(SCALE_TYPE_NAME, string="Tipe", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('rapel', "Rapel Belum Diproses"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan"),
    ], string="Status", default='draft', required=True, track_visibility='onchange')
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
    ], string="Status Rapel", default='0', required=True, readonly=True)
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.scale.period', string="Ref. Rapel", readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True,
                                         readonly=True, default=lambda self: self.env.user.company_id,
                                         states={'draft': [('readonly', False)]})
    scale_ids = fields.One2many('ka_hr_payroll.scale', 'period_id', string="Data Skala")

    def _get_type_name(self, key):
        """To get type name of `scale_type` value.

        Arguments:
            key {String} -- `scale_type` value.

        Returns:
            String -- Result of `scale_type` value check.
        """
        for _type in self.SCALE_TYPE_NAME:
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
        period = super(KaHrPayrollScalePeriod, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            type_name = self._get_type_name(period.scale_type)
            date_start_obj = datetime.strptime(period.date_start, DATE_FORMAT)
            date_start_str = date_start_obj.strftime('%d-%m-%Y')
            period.name = "Skala {0} {1} Periode: {2}".format(type_name, period.status_id.name, date_start_str)
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
        """Set state to `processed` then generate lines.

        Decorators:
            api.multi
        """
        if len(self.scale_ids) <= 0:
            raise ValidationError("Anda harus memasukkan data skala terlebih dahulu!")
        else:
            for scale in self.scale_ids:
                if scale.state == 'draft':
                    raise ValidationError("Ada data skala yang belum diproses!")
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

    def get_last_period(self, status_id, scale_type, company_payroll_id, config=None):
        """To get last period which `state = done`.

        Arguments:
            status_id {Int} -- ID of `hr.status`.
            scale_type {String} -- Type of scale. It can be 'gp', 'tr' or 'tj'.
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
        date_config_str = date_config.strftime(DATE_FORMAT) + ' 00:00:00'

        return self.search([
            ('date_start', '<=', fields.Date.today()),
            ('status_id', 'parent_of', status_id),
            ('scale_type', '=', scale_type),
            ('state', '=', 'done'),
            ('state_rapel', '!=', '1'),
            ('date_done', '<', date_config_str),
            ('company_payroll_id', '=', company_payroll_id),
        ], limit=1, order='date_start desc')

    def generate_rapel(self):
        """To generate rapel, based on new period of scale and last period of scale.

        Raises:
            ValidationError -- Raise when last scale not found.
        """
        config = self.env['ka_hr_payroll.config'].default_config()
        last_period = self.get_last_period(self.status_id.id, self.scale_type, self.company_payroll_id.id,
                                           config=config)
        if last_period:
            type_name = self._get_type_name(self.scale_type)
            date_done = datetime.strptime(self.date_done, DATETIME_FORMAT)

            if date_done.day > config.date_end:
                date_pay = date_done + relativedelta(months=1)
            else:
                date_pay = date_done

            data_rapel_period = {
                'new_period_id': self.id,
                'scale_type': self.scale_type,
                'old_period_id': last_period.id,
                'date_start': get_utc_timezone(self.date_start + ' 00:00:00'),
                'date_end': self.date_done,
                'year_pay': str(date_pay.year),
                'month_pay': date_pay.month,
                'status_id': self.status_id.id,
                'company_payroll_id': self.company_payroll_id.id,
            }

            rapel_period = self.env['ka_hr_payroll.rapel.scale.period'].create(data_rapel_period)
            self.rapel_id = rapel_period

            for scale in self.scale_ids:
                scale.generate_rapel(last_period.id, rapel_period.id)

            self.state_rapel = '2'
            self.env.user.notify_info("Rapel Skala {0} berhasil dibuat!".format(type_name))
        else:
            raise ValidationError("Data periode lama tidak ditemukan! Anda tidak dapat melanjutkan aksi ini.")

    @api.multi
    def action_done(self):
        """Generate rapel then set `state` to `done` and `date_done` to date now.

        Decorators:
            api.multi
        """
        if not self.date_done:
            self.date_done = fields.Date.today()
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

    @api.multi
    def action_view_scale(self):
        """To view all `ka_hr_payroll.scale` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        action = self.env.ref('ka_hr_payroll.action_scale')
        result = action.read()[0]
        result['domain'] = [('period_id', '=', self.id)]
        result['context'] = {'default_period_id': self.id}
        return result

    @api.multi
    def action_create_scale(self):
        """To open create form `ka_hr_payroll.scale` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        view_id = self.env.ref('ka_hr_payroll.view_scale_form').id
        action = self.env.ref('ka_hr_payroll.action_scale')
        result = action.read()[0]
        result['views'] = [(view_id, 'form')]
        result['view_id'] = view_id
        result['domain'] = [('period_id', '=', self.id)]
        result['context'] = {'default_period_id': self.id}
        return result

    def generate_dummy(self):
        data_scale_period = [
            (
                '2017-01-01', '02', 'gp', '1', '2017-01-03 00:00:00', '2017-01-03 00:00:00', [
                    (1, 4, 48, 4.048, 1000000, 2000, 1),
                    (1, 4, 48, 4.048, 1100000, 2500, 2),
                    (1, 4, 48, 4.048, 1200000, 3000, 3),
                    (1, 4, 48, 4.048, 1300000, 3500, 4),
                    (1, 4, 48, 4.048, 1400000, 4000, 5),
                    (1, 5, 48, 5.024, 1500000, 4500, 6),
                    (1, 5, 48, 5.024, 1600000, 5000, 7)]
            ),
            (
                '2017-01-01', '02', 'tj', '1', '2017-01-03 00:00:00', '2017-01-03 00:00:00', [
                    (1, 4, 48, 4.048, 100000, 1000, 1),
                    (1, 4, 48, 4.048, 110000, 1500, 2),
                    (1, 4, 48, 4.048, 120000, 2000, 3),
                    (1, 4, 48, 4.048, 130000, 2500, 4),
                    (1, 4, 48, 4.048, 140000, 3000, 5),
                    (1, 5, 48, 5.024, 150000, 3500, 6),
                    (1, 5, 48, 5.024, 160000, 4000, 7)]
            ),
            (
                '2017-01-01', '02', 'tr', '1', '2017-01-03 00:00:00', '2017-01-03 00:00:00', [
                    (1, 4, 48, 4.048, 200000, 2000, 1),
                    (1, 4, 48, 4.048, 220000, 2500, 2),
                    (1, 4, 48, 4.048, 240000, 3000, 3),
                    (1, 4, 48, 4.048, 260000, 3500, 4),
                    (1, 4, 48, 4.048, 280000, 4000, 5),
                    (1, 5, 48, 5.024, 300000, 4500, 6),
                    (1, 5, 48, 5.024, 320000, 5000, 7)]
            ),
        ]

        for date_start, status_code, scale_type, company_payroll_code, date_approve, date_done, data_scale in data_scale_period:
            status_id = self.env['hr.status'].search([('code', '=', status_code)], limit=1)
            company_payroll_id = self.env['res.company'].search([('code', '=', company_payroll_code)], limit=1)
            data = {
                'date_start': date_start,
                'status_id': status_id.id,
                'scale_type': scale_type,
                'company_payroll_id': company_payroll_id.id,
                'date_approve': date_approve,
                'date_done': date_done,
            }
            scale_period = self.create(data)

            for min_scale, max_scale, max_row_scale, max_value_scale, value, delta, golongan in data_scale:
                data = {
                    'min_scale': min_scale,
                    'max_scale': max_scale,
                    'max_row_scale': max_row_scale,
                    'max_value_scale': max_value_scale,
                    'value_start': value,
                    'delta': delta,
                    'golongan_id': golongan,
                    'period_id': scale_period.id,
                }
                scale = self.env['ka_hr_payroll.scale'].create(data)
                scale.action_process()

            scale_period.action_process()
            scale_period.action_approve()


class KaHrPayrollScale(models.Model):
    """Data of scale. It can be base salary scale, or allowance scale.

    _name = 'ka_hr_payroll.scale'
    """

    _name = 'ka_hr_payroll.scale'
    _description = "Data skala karyawan"
    _order = 'golongan_id asc'
    _inherit = 'mail.thread'

    SCALE_TYPE_NAME = [
        ('gp', "Gaji Pokok"),
        ('tr', "Tunj. Rumah"),
        ('tj', "Tunj. Jabatan"),
    ]

    name = fields.Char(string="Nama Skala", size=255)
    min_scale = fields.Integer(string="Skala Awal", required=True, readonly=True,
                               default=1, states={'draft': [('readonly', False)]})
    max_scale = fields.Integer(string="Skala Akhir", required=True, readonly=True,
                               default=4, states={'draft': [('readonly', False)]})
    max_row_scale = fields.Integer(string="Maks. Baris Skala", required=True, readonly=True,
                                   default=48, states={'draft': [('readonly', False)]})
    # max_value_scale = fields.Float(string="Nilai Max. Skala", compute='_compute_scale',
    #     digits=(6, 3), readonly=True, states={'draft': [('readonly', False)]}, store=True,
    #     help="Jika diisi maka skala punya nilai maksimal. Jika tidak diisi maka nilai maksimal skala tergantung dari Skala akhir & Maks. baris skala.")
    max_value_scale = fields.Float(string="Nilai Max. Skala", digits=(6, 3), readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help="Jika diisi maka skala punya nilai maksimal. Jika tidak diisi maka nilai maksimal skala tergantung dari Skala akhir & Maks. baris skala.")
    value_start = fields.Float(string="Nilai Awal", required=True, readonly=True,
                               states={'draft': [('readonly', False)]})
    delta = fields.Float(string="Nilai Delta", required=True, readonly=True,
                         states={'draft': [('readonly', False)]})
    golongan_id = fields.Many2one('hr.golongan', string="Golongan", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Sudah Diproses"),
    ], string="Status Skala", default='draft', required=True)
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.scale', string="Ref. Rapel", readonly=True)
    line_ids = fields.One2many('ka_hr_payroll.scale.lines', 'scale_id', readonly=True,
                               states={'draft': [('readonly', False)]})

    # start of related fields
    period_id = fields.Many2one('ka_hr_payroll.scale.period', string="Periode Skala", required=True,
                                readonly=True, states={'draft': [('readonly', False)]}, ondelete='cascade')
    date_start = fields.Date(string="Tanggal Mulai", related='period_id.date_start', readonly=True)
    scale_type = fields.Selection(SCALE_TYPE_NAME, string="Tipe", related='period_id.scale_type', readonly=True)
    status_id = fields.Many2one('hr.status', string="Status Karyawan", related='period_id.status_id',
                                readonly=True)
    state_period = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('rapel', "Rapel Belum Diproses"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan"),
    ], string="Status Periode", related='period_id.state', readonly=True, store=True)
    date_approve = fields.Datetime(string="Tanggal Disetujui", related='period_id.date_approve', readonly=True)
    date_done = fields.Datetime(string="Tanggal Berlaku", related='period_id.date_done', readonly=True)
    notes = fields.Text(string="Catatan Persetujuan", related='period_id.notes', readonly=True)
    state_rapel = fields.Selection([
        ('0', "Tidak Ada Rapel"),
        ('1', "Rapel Belum Diproses"),
        ('2', "Rapel Sudah Diproses"),
    ], string="Status Rapel", related='period_id.state_rapel', readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         related='period_id.company_payroll_id', readonly=True)

    _sql_constraints = [
        ('ka_hr_payroll_scale_unique', 'UNIQUE(period_id, golongan_id)',
         "Data skala sudah ada! Anda tidak bisa melanjutkan aksi ini.")
    ]

    def _get_type_name(self, key):
        """To get type name of `scale_type` value.

        Arguments:
            key {String} -- `scale_type` value.

        Returns:
            String -- Result of `scale_type` value check.
        """
        for _type in self.SCALE_TYPE_NAME:
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
        scale = super(KaHrPayrollScale, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            if not scale.max_value_scale:
                scale.max_value_scale = scale.max_scale + (scale.max_row_scale / 1000)
            type_name = self._get_type_name(scale.scale_type)
            date_obj = datetime.strptime(scale.date_start, DATE_FORMAT)
            date_str = date_obj.strftime('%d-%m-%Y')
            scale.name = "Skala {0} {1} Golongan {2} Periode: {3}".format(type_name, scale.status_id.name,
                                                                          scale.golongan_id.name, date_str)
        return scale

    # @api.depends('max_scale', 'max_row_scale')
    # def _compute_scale(self):
    #     for scale in self:
    #         if not scale.max_value_scale:
    #             scale.max_value_scale = scale.max_scale + (scale.max_row_scale / 1000)

    @api.multi
    def action_draft(self):
        """Set state to `draft` then delete related lines

        Decorators:
            api.multi
        """
        if self.state == 'draft':
            return

        if self.state_period != 'draft':
            raise ValidationError("Data periode sudah diproses! Anda tidak bisa melakukan aksi ini.")

        self.state = 'draft'
        for line in self.line_ids:
            line.unlink()

    def action_generate_lines(self):
        """Generate lines of this model

        Decorators:
            @api.multi
        """
        vs = self.value_start
        for i in range(self.min_scale, self.max_scale + 1):
            for row in range(self.max_row_scale + 1):
                scale = float(i + (row * 0.001))
                if self.max_value_scale and self.max_value_scale < scale:
                    break

                self.env['ka_hr_payroll.scale.lines'].create({
                    'scale_id': self.id,
                    'scale': scale,
                    'value': vs,
                })
                vs += self.delta
        self.env.user.notify_info("Data skala berhasil diproses!")

    @api.multi
    def action_process(self):
        """Set state to `processed` then generate lines.

        Decorators:
            api.multi
        """
        if self.state == 'processed':
            return

        if self.min_scale > 10.0 or self.max_scale > 10.0:
            raise ValidationError("Ada kesalahan pada penulisan skala. Skala tidak boleh > 10.0")

        self.state = 'processed'
        self.action_generate_lines()

    def get_last_scale(self, period_id, golongan_id):
        """To get last scale which `state = processed`.

        Arguments:
            period_id {Int} -- ID of `ka_hr_payroll.scale.period`.
            golongan_id {Int} -- ID of `hr.golongan`.

        Returns:
            Recordset -- Result of query with limit `1`.
        """
        return self.search([
            ('period_id', '=', period_id),
            ('golongan_id', '=', golongan_id),
            ('state', '=', 'processed'),
        ], limit=1)

    def generate_rapel(self, last_period_id, rapel_period_id):
        """To generate rapel of this scale period.

        Arguments:
            last_period_id {Int} -- ID this model parent from `ka_hr_payroll.scale.period`.
            rapel_period_id {Int} -- ID of `ka_hr_payroll.rapel.scale.period` which generated from this parent.
        """
        last_scale = self.get_last_scale(last_period_id, self.golongan_id.id)
        data_rapel_scale = {
            'rapel_period_id': rapel_period_id,
            'new_scale_id': self.id,
        }

        if last_scale:
            data_rapel_scale['old_scale_id'] = last_scale.id

        rapel_scale = self.env['ka_hr_payroll.rapel.scale'].create(data_rapel_scale)
        self.rapel_id = rapel_scale

        for line in self.line_ids:
            line.generate_rapel(last_scale.id, self.rapel_id.id)


class KaHrPayrollScaleLines(models.Model):
    """Data lines of scale (detail skala).

    _name = 'ka_hr_payroll.scale.lines'
    """

    _name = 'ka_hr_payroll.scale.lines'

    name = fields.Char(string="Nama Detail", size=255)
    scale_id = fields.Many2one('ka_hr_payroll.scale', string="Skala",
                               required=True, ondelete='cascade')
    scale = fields.Float(string="Nilai Skala", digits=(6, 3), required=True)
    value = fields.Float(string="Nilai", required=True)

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
        lines = super(KaHrPayrollScaleLines, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            lines.name = "Detail {0}".format(lines.scale_id.name)
        return lines

    def get_last_lines(self, scale_id, scale):
        """To get last lines before this record.

        Arguments:
            scale_id {Int} -- ID of this model parent from `ka_hr_payroll.scale`.
            scale {Int} -- Scale value.

        Returns:
            Recordset -- Result of query with `limit=1`.
        """
        return self.search([
            ('scale_id', '=', scale_id),
            ('scale', '=', scale),
        ], limit=1)

    def generate_rapel(self, last_scale_id, rapel_scale_id):
        """To generate rapel scale lines.

        Arguments:
            last_scale_id {Int} -- ID this model parent from `ka_hr_payroll.scale`.
            rapel_scale_id {Int} -- ID of `ka_hr_payroll.rapel.scale` which generated from this parent.
        """
        last_lines = self.get_last_lines(last_scale_id, self.scale)
        data_rapel_lines = {
            'rapel_scale_id': rapel_scale_id,
            'new_scale_lines_id': self.id,
            'new_value': self.value,
            'scale': self.scale,
        }

        if last_lines:
            data_rapel_lines['old_scale_lines_id'] = last_lines.id
            data_rapel_lines['old_value'] = last_lines.value

        self.env['ka_hr_payroll.rapel.scale.lines'].create(data_rapel_lines)
