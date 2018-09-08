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


class KaHrPayrollCompanyKonjungtur(models.Model):
    """Data of company konjungtur period.

    _name = 'ka_hr_payroll.company.konjungtur'
    """

    _name = 'ka_hr_payroll.company.konjungtur'
    _description = "Set Unit/PG Konjungtur Gaji / Dapen"
    _order = 'date_start desc'
    _inherit = 'mail.thread'

    _KONJUNGTUR_TYPE_NAME = [
        ('1', "Konjungtur Gaji"),
        ('2', "Konjungtur Dapen"),
    ]

    name = fields.Char(string="Nama", size=255)
    date_start = fields.Date(string="Tanggal Mulai", required=True, readonly=True,
                             default=fields.Date.today, states={'draft': [('readonly', False)]})
    value = fields.Float(string="Nilai Konjungtur (%)", required=True, readonly=True,
                         default=100.00, states={'draft': [('readonly', False)]})
    konjungtur_type = fields.Selection(_KONJUNGTUR_TYPE_NAME, string="Tipe", required=True, readonly=True,
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
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.company.konjungtur', string="Ref. Rapel", readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         default=lambda self: self.env.user.company_id,
                                         states={'draft': [('readonly', False)]})

    def _get_konjungtur_type_name(self, key):
        """To get type name of `konjungtur_type` value.

        Arguments:
            key {String} -- `konjungtur_type` value.

        Returns:
            String -- Result of `konjungtur_type` value check.
        """
        for name in self._KONJUNGTUR_TYPE_NAME:
            if name[0] == key:
                return name[1]
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
        konjungtur = super(KaHrPayrollCompanyKonjungtur, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_start_obj = datetime.strptime(konjungtur.date_start, DATE_FORMAT)
            date_start_str = date_start_obj.strftime('%d-%m-%Y')
            type_name = self._get_konjungtur_type_name(konjungtur.konjungtur_type)
            konjungtur.name = "{0} Periode: {1}".format(type_name, date_start_str)
        return konjungtur

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

    def get_last_konjungtur(self, konjungtur_type, company_payroll_id, config=None, payroll_date=None):
        """To get last konjungtur which `state = done`.

        Arguments:
            konjungtur_type {String} -- `konjungtur_type` value.
            company_payroll_id {Int} -- ID of `res.company`.
            config {Recordset} -- Result from `ka_hr_payroll.config` `default_config()`.

        Returns:
            Recordset -- Record of last konjungtur
        """
        if not config:
            config = self.env['ka_hr_payroll.config'].default_config()

        if not payroll_date:
            date_now = datetime.now().date()
            date_config = datetime.strptime("{0}-{1}-{2}".format(date_now.year, date_now.month, config.date_start),
                                            DATE_FORMAT)
        else:
            if isinstance(payroll_date, basestring):
                payroll_date_obj = datetime.strptime(payroll_date, DATE_FORMAT)
            else:
                payroll_date_obj = payroll_date
            date_config = datetime.strptime("{0}-{1}-{2}".format(payroll_date_obj.year, payroll_date_obj.month, config.date_start),
                                                DATE_FORMAT)
        date_config_str = date_config.strftime(DATE_FORMAT)

        return self.search([
            ('date_start', '<=', fields.Date.today()),
            ('konjungtur_type', '=', konjungtur_type),
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
        last_konjungtur = self.get_last_konjungtur(self.konjungtur_type, self.company_payroll_id.id, config=config)
        if last_konjungtur:
            date_done = datetime.strptime(self.date_done, DATETIME_FORMAT)

            if date_done.day > config.date_end:
                date_pay = date_done + relativedelta(months=1)
            else:
                date_pay = date_done

            data_rapel = {
                'new_konjungtur_id': self.id,
                'old_konjungtur_id': last_konjungtur.id,
                'konjungtur_type': self.konjungtur_type,
                'date_start': get_utc_timezone(self.date_start + ' 00:00:00'),
                'date_end': self.date_done,
                'year_pay': str(date_pay.year),
                'month_pay': date_pay.month,
                'new_value': self.value,
                'old_value': last_konjungtur.value,
                'company_payroll_id': self.company_payroll_id.id,
            }

            rapel_konjungtur = self.env['ka_hr_payroll.rapel.company.konjungtur'].create(data_rapel)
            self.rapel_id = rapel_konjungtur
            self.state_rapel = '2'
            self.env.user.notify_info("Rapel konjungtur berhasil dibuat!")
        else:
            raise ValidationError("Data konjungtur lama tidak ditemukan! Anda tidak dapat melanjutkan aksi ini.")

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
        """Set `state='canceled'`.
        """
        self.state = 'canceled'

    def generate_dummy(self):
        data_gaji = {
            'date_start': '2017-01-01',
            'value': 120.00,
            'konjungtur_type': '1',
            'date_approve': '2017-01-03 00:00:00',
            'date_done': '2017-01-03 00:00:00',
            'company_payroll_id': 3,
        }
        konjungtur_gaji = self.create(data_gaji)
        konjungtur_gaji.action_process()
        konjungtur_gaji.action_approve()

        data_dapen = {
            'date_start': '2017-01-01',
            'value': 85.00,
            'konjungtur_type': '2',
            'date_approve': '2017-01-03 00:00:00',
            'date_done': '2017-01-03 00:00:00',
            'company_payroll_id': 3,
        }
        konjungtur_dapen = self.create(data_dapen)
        konjungtur_dapen.action_process()
        konjungtur_dapen.action_approve()
