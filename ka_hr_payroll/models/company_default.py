# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError
from ..helpers import get_utc_timezone, check_rapel_status


class KaHrPayrollCompanyDefault(models.Model):
    """Data of company default value for payroll.

    _name = 'ka_hr_payroll.company.default'
    """

    _name = 'ka_hr_payroll.company.default'
    _description = "Setting ketetapan gaji default Unit/PG"
    _order = 'date_start desc'
    _inherit = 'mail.thread'

    name = fields.Char(string="Nama", size=255)
    date_start = fields.Date(string="Tanggal Mulai", required=True, readonly=True,
                             default=fields.Date.today, states={'draft': [('readonly', False)]})
    status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True, readonly=True,
                                states={'draft': [('readonly', False)]})
    gaji_pokok = fields.Float(string="Gaji Pokok", required=True, readonly=True, default=0.0,
                              states={'draft': [('readonly', False)]})
    tunjangan_rumah = fields.Float(string="Tunj. Rumah", required=True, readonly=True, default=0.0,
                                   states={'draft': [('readonly', False)]})
    tunjangan_jabatan = fields.Float(string="Tunj. Jabatan", required=True, readonly=True, default=0.0,
                                     states={'draft': [('readonly', False)]})
    tunjangan_khusus = fields.Float(string="Tunj. Khusus", required=True, readonly=True, default=0.0,
                                    states={'draft': [('readonly', False)]})
    tunjangan_representasi = fields.Float(string="Tunj. Representasi", required=True, readonly=True, default=0.0,
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
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.company.default', string="Ref. Rapel", readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         default=lambda self: self.env.user.company_id,
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
        record = super(KaHrPayrollCompanyDefault, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_obj = datetime.strptime(record.date_start, DATE_FORMAT)
            date_str = date_obj.strftime('%d-%m-%Y')
            record.name = "Ketetapan Gaji {0}. Periode: {1}".format(record.status_id.name, date_str)
        return record

    def action_draft(self):
        """Set state to `draft`.
        """
        self.state = 'draft'

    def action_process(self):
        """Set state to `processed` then generate lines.
        """
        self.state = 'processed'

    def action_approve(self):
        """Check rapel and set state to `rapel` or `done`.
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
        """
        self.state = 'rapel'
        self.state_rapel = '1'

    def get_last_default(self, status_id, company_payroll_id, config=None):
        """To get last konjungtur which `state = done`.

        Arguments:
            status_id {Int} -- ID of `hr.status`.
            company_payroll_id {Int} -- ID of `res.company`.
            config {Recordset} -- Result from `ka_hr_payroll.config` `default_config()`.

        Returns:
            [type] -- [description]
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
        """To generate rapel, based on new and last konjungtur.

        Raises:
            ValidationError -- Raise when last scale not found.
        """
        config = self.env['ka_hr_payroll.config'].default_config()
        last_default = self.get_last_default(self.status_id.id, self.company_payroll_id.id, config=config)
        if last_default:
            date_done = datetime.strptime(self.date_done, DATETIME_FORMAT)

            if date_done.day > config.date_end:
                date_pay = date_done + relativedelta(months=1)
            else:
                date_pay = date_done

            data_rapel = {
                'new_company_default_id': self.id,
                'old_company_default_id': last_default.id,
                'date_start': get_utc_timezone(self.date_start + ' 00:00:00'),
                'date_end': self.date_done,
                'year_pay': str(date_pay.year),
                'month_pay': date_pay.month,
                'new_gaji_pokok': self.gaji_pokok,
                'new_tunjangan_rumah': self.tunjangan_rumah,
                'new_tunjangan_jabatan': self.tunjangan_jabatan,
                'new_tunjangan_khusus': self.tunjangan_khusus,
                'new_tunjangan_representasi': self.tunjangan_representasi,
                'old_gaji_pokok': last_default.gaji_pokok,
                'old_tunjangan_rumah': last_default.tunjangan_rumah,
                'old_tunjangan_jabatan': last_default.tunjangan_jabatan,
                'old_tunjangan_khusus': last_default.tunjangan_khusus,
                'old_tunjangan_representasi': last_default.tunjangan_representasi,
                'status_id': self.status_id.id,
                'company_payroll_id': self.company_payroll_id.id,
            }

            rapel_default = self.env['ka_hr_payroll.rapel.company.default'].create(data_rapel)
            self.rapel_id = rapel_default
            self.state_rapel = '2'
            self.env.user.notify_info("Rapel ketetapan berhasil dibuat!")
        else:
            raise ValidationError("Data ketetapan lama tidak ditemukan! Anda tidak dapat melanjutkan aksi ini.")

    def action_done(self):
        """Generate rapel then set `state` to `done` and `date_done` to date now.
        """
        if not self.date_done:
            self.date_done = fields.Datetime.now()
        if self.state_rapel == '1':
            self.generate_rapel()
        self.state = 'done'

    def action_cancel(self):
        """Set `state='canceled'`.
        """
        self.state = 'canceled'
