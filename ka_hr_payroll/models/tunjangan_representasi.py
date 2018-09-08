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


class KaHrPayrollTunjanganRepresentasi(models.Model):
    """Data of representative allowance (Tunjangan Representasi) of employee.

    _name = 'ka_hr_payroll.tunjangan.representasi'
    """

    _name = 'ka_hr_payroll.tunjangan.representasi'
    _description = "Data tunjangan representasi karyawan"
    _order = 'date_start desc'
    _inherit = 'mail.thread'

    name = fields.Char(string="Nama", size=255)
    date_start = fields.Date(string="Tanggal Mulai", required=True, readonly=True,
                             default=fields.Date.today, states={'draft': [('readonly', False)]})
    status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True, readonly=True,
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
    ], string="Status Rapel", default='0', readonly=True)
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.tunjangan.representasi', string="Referensi Rapel",
                               readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         default=lambda self: self.env.user.company_id,
                                         states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('ka_hr_payroll.tunjangan.representasi.lines', 'tunjangan_id',
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
        tunjangan = super(KaHrPayrollTunjanganRepresentasi, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_start_obj = datetime.strptime(tunjangan.date_start, DATE_FORMAT)
            date_start_str = date_start_obj.strftime('%d-%m-%Y')
            tunjangan.name = "Tunj. Representasi Periode: {0}".format(date_start_str)
        return tunjangan

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
        """Set state to `rapel`.

        Decorators:
            api.multi
        """
        self.state = 'rapel'
        self.state_rapel = '1'

    def get_last_tunjangan(self, status_id, company_payroll_id, config=None):
        """To get last tunjangan representasi.

        Arguments:
            status_id {Int} -- ID of `hr.status`.
            company_payroll_id {Int} -- ID of `res.company`.
            config {Recordset} -- Result from `ka_hr_payroll.config` `default_config()`.

        Returns:
            Recordset -- Result of search last periode.
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
            ('company_payroll_id', '=', company_payroll_id),
        ], limit=1, order='date_start desc')

    def generate_rapel(self):
        """To generate rapel, based on new tunjangan representasi & old tunjangan representasi.

        Raises:
            ValidationError -- Raise when last scale not found.
        """
        config = self.env['ka_hr_payroll.config'].default_config()
        last_tunjangan = self.get_last_tunjangan(self.status_id.id, self.company_payroll_id.id, config=config)
        if last_tunjangan:
            date_done = datetime.strptime(self.date_done, DATETIME_FORMAT)

            if date_done.day > config.date_end:
                date_pay = date_done + relativedelta(months=1)
            else:
                date_pay = date_done

            data_rapel = {
                'new_tunjangan_id': self.id,
                'old_tunjangan_id': last_tunjangan.id,
                'date_start': get_utc_timezone(self.date_start + ' 00:00:00'),
                'date_end': self.date_done,
                'year_pay': str(date_pay.year),
                'month_pay': date_pay.month,
                'status_id': self.status_id.id,
                'company_payroll_id': self.company_payroll_id.id,
            }

            rapel_tunjangan = self.env['ka_hr_payroll.rapel.tunjangan.representasi'].create(data_rapel)
            self.rapel_id = rapel_tunjangan

            for line in self.line_ids:
                line.generate_rapel(last_tunjangan.id, rapel_tunjangan.id)

            self.state_rapel = '2'
            self.env.user.notify_info("{0}, berhasil dibuat!".format(rapel_tunjangan.name))
        else:
            raise ValidationError(
                "Data Tunjangan Representasi yang lama tidak ditemukan, anda tidak dapat melanjutkan aksi ini.")

    @api.multi
    def action_done(self):
        """Set state to `done`.

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
        detail = [
            ('10', 2800000),
            ('11', 2500000),
            ('13', 1850000),
            ('14', 1650000),
            ('08', 5000000),
            ('09', 4500000),
        ]
        for jabatan_code, value in detail:
            jabatan = self.env['hr.jabatan'].search([('code', '=', jabatan_code)], limit=1)
            self.env['ka_hr_payroll.tunjangan.representasi.lines'].create({
                'tunjangan_id': tunjangan.id,
                'jabatan_id': jabatan.id,
                'value': value,
            })
        tunjangan.action_process()
        tunjangan.action_approve()


class KaHrPayrollTunjanganRepresentasiLines(models.Model):
    """Lines of `ka_hr_payroll.tunjangan.representasi`.

    _name = 'ka_hr_payroll.tunjangan.representasi.lines'
    """

    _name = 'ka_hr_payroll.tunjangan.representasi.lines'

    name = fields.Char(string="Nama", size=255)
    tunjangan_id = fields.Many2one('ka_hr_payroll.tunjangan.representasi', string="Periode Tunj. Representasi",
                                   required=True)
    jabatan_id = fields.Many2one('hr.jabatan', string="Jabatan", required=True)
    value = fields.Float(string="Nilai", required=True)

    _sql_constraints = [
        ('tunjangan_representasi_lines_unique', 'UNIQUE(tunjangan_id, jabatan_id)', "Data jabatan sudah ada!")
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
        lines = super(KaHrPayrollTunjanganRepresentasiLines, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            lines.name = "Detail {0}".format(lines.tunjangan_id.name)
        return lines

    def get_last_lines(self, tunjangan_id, jabatan_id):
        """To get last lines before this record.

        Arguments:
            tunjangan_id {Int} -- ID of this model parent from `ka_hr_payroll.tunjangan.representasi`.
            jabatan_id {Int} -- ID of `hr.jabatan`.

        Returns:
            Recordset -- Result of query with `limit=1`.
        """
        return self.search([
            ('tunjangan_id', '=', tunjangan_id),
            ('jabatan_id', '=', jabatan_id),
        ], limit=1)

    def generate_rapel(self, last_tunjangan_id, rapel_id):
        """To generate rapel tunjangan representasi lines.

        Arguments:
            last_tunjangan_id {Int} -- ID this model parent from `ka_hr_payroll.tunjangan.representasi`.
            rapel_id {Int} -- ID of `ka_hr_payroll.rapel.tunjangan.representasi` which generated from this parent.
        """
        last_lines = self.get_last_lines(last_tunjangan_id, self.jabatan_id.id)
        data_rapel_lines = {
            'rapel_id': rapel_id,
            'new_tunjangan_lines_id': self.id,
            'jabatan_id': self.jabatan_id.id,
            'new_value': self.value,
        }

        if last_lines:
            data_rapel_lines['old_tunjangan_lines_id'] = last_lines.id
            data_rapel_lines['old_value'] = last_lines.value

        self.env['ka_hr_payroll.rapel.tunjangan.representasi.lines'].create(data_rapel_lines)
