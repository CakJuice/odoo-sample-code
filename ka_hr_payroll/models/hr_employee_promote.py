# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from ..helpers import get_utc_timezone, check_rapel_status


class KaHrPayrollEmployeePromote(models.Model):
    """Data history of employee promote.

    _inherit = 'hr.employee.promote'
    """

    _inherit = 'hr.employee.promote'
    _order = 'date_start desc'

    scale = fields.Float(string="Skala Baru", digits=(6, 3), readonly=True,
                         states={'draft': [('readonly', False)]})
    # japres = fields.Float(string="Jasa Prestasi", digits=(5, 2), default=0.00, readonly=True,
    #     states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('rapel', "Rapel Belum Diproses"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan"),
    ], string="Status", default='draft', required=True, track_visibility='onchange')
    # date_approve = fields.Datetime(string="Tanggal Disetujui", readonly=True,
    #     states={'processed': [('readonly', False)]})
    date_approve = fields.Datetime(string="Tanggal Disetujui",
                                   states={'done': [('readonly', True)], 'canceled': [('readonly', True)]})
    date_done = fields.Datetime(string="Tanggal Berlaku",
                                states={'done': [('readonly', True)], 'canceled': [('readonly', True)]})
    state_rapel = fields.Selection([
        ('0', "Tidak Ada Rapel"),
        ('1', "Rapel Belum Diproses"),
        ('2', "Rapel Sudah Diproses"),
    ], string="Status Rapel", default='0', required=True, readonly=True)
    rapel_id = fields.Many2one('ka_hr_payroll.rapel.hr.employee.promote', string="Ref. Rapel", readonly=True)
    periodic_promote_id = fields.Many2one('ka_hr_payroll.company.periodic.promote.employee',
                                          string="Ref. Kenaikan Berkala")

    old_scale = fields.Float(string="Skala Lama", compute='_compute_old_promote', digits=(6, 3), store=True)
    # old_japres = fields.Float(string="Jasa Prestasi Lama", compute='_compute_old_promote', digits=(5, 2), store=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         compute='_compute_employee', store=True)

    @api.depends('employee_id')
    def _compute_employee(self):
        for promote in self:
            promote.company_payroll_id = promote.employee_id.company_payroll_id

    def get_last_processed_promote(self, employee_id, date_start=None):
        """Override.
        To get data processed promote of employee.

        Arguments:
            employee_id {Int} -- ID of `hr.employee`.

        Returns:
            Recordset -- Result of query with limit `1` and order by `date_start desc`.
        """
        if not date_start:
            date_start = fields.Date.today()
        return self.search([
            ('date_start', '<=', date_start),
            ('employee_id', '=', employee_id),
            ('promote_type', 'not in', ['6', '7', '8', '9']),
            ('state', 'in', ['processed', 'rapel', 'done']),
        ], limit=1, order='date_start desc')

    def action_approve(self):
        """Override.
        Check rapel and set state to `rapel` or `done`.
        """
        if not self.date_approve:
            self.date_approve = fields.Datetime.now()

        if self.promote_type in ['6', '7', '8', '9']:
            # pensiun langsung done
            self.action_done()
        else:
            config = self.env['ka_hr_payroll.config'].default_config()
            is_recruitment = True if self.promote_type == '4' else False
            is_extended = True if self.promote_type == '5' else False
            check = check_rapel_status(self, config, is_recruitment=is_recruitment, is_extended=is_extended)
            if check:
                self.action_rapel()
            else:
                self.action_done()

    def action_rapel(self):
        """Set `state = 'rapel'` and `state_rapel = '2'`.
        """
        self.state = 'rapel'
        self.state_rapel = '1'

    def get_last_promote(self, employee_id, config=None):
        """To get data promote of employee.

        Arguments:
            employee_id {Int} -- ID of `hr.employee`.
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
            ('employee_id', '=', employee_id),
            ('promote_type', 'not in', ['6', '7', '8', '9']),
            ('state', '=', 'done'),
            ('state_rapel', '!=', '1'),
            ('date_done', '<', date_config_str),
        ], limit=1, order='date_start desc')

    def generate_rapel(self):
        """To generate rapel, for this employee promote.

        Raises:
            ValidationError -- Raise when last scale not found.
        """
        if not self.old_promote_id:
            raise ValidationError("Data history lama tidak ditemukan! Anda tidak dapat melanjutkan aksi ini.")

        config = self.env['ka_hr_payroll.config'].default_config()
        date_done = datetime.strptime(self.date_done, DATETIME_FORMAT)

        if date_done.day > config.date_end:
            date_pay = date_done + relativedelta(months=1)
        else:
            date_pay = date_done

        data_rapel = {
            'new_employee_promote_id': self.id,
            'old_employee_promote_id': self.old_promote_id.id,
            'date_start': get_utc_timezone(self.date_start + ' 00:00:00'),
            'date_end': self.date_done,
            'year_pay': str(date_pay.year),
            'month_pay': date_pay.month,
            'company_payroll_id': self.company_payroll_id.id,
        }
        rapel_promote = self.env['ka_hr_payroll.rapel.hr.employee.promote'].create(data_rapel)
        self.rapel_id = rapel_promote
        self.state_rapel = '2'
        self.env.user.notify_info("Rapel History: {0} berhasil dibuat!".format(self.name))

    def _clean_old_value(self, obj):
        super(KaHrPayrollEmployeePromote, self)._clean_old_value(obj)
        obj.scale = None
        # obj.japres = None

    def _assign_new_value(self, obj, assign_obj):
        super(KaHrPayrollEmployeePromote, self)._assign_new_value(obj, assign_obj)
        obj.old_scale = assign_obj.scale
        # obj.old_japres = assign_obj.japres

    def _assign_old_value(self, obj, assign_obj):
        super(KaHrPayrollEmployeePromote, self)._assign_old_value(obj, assign_obj)
        obj.old_scale = assign_obj.old_scale
        # obj.old_japres = assign_obj.old_japres

    def _assign_employee_old_value(self):
        super(KaHrPayrollEmployeePromote, self)._assign_employee_old_value()
        self.employee_id.scale = self.old_scale
        # self.employee_id.japres = self.old_japres

    def _assign_employee_new_value(self):
        super(KaHrPayrollEmployeePromote, self)._assign_employee_new_value()
        self.employee_id.scale = self.scale
        # self.employee_id.japres = self.japres

    def action_done(self):
        """Override.
        Generate rapel then set `state` to `done` and `date_done` to date now.
        """
        super(KaHrPayrollEmployeePromote, self).action_done()
        if self.state_rapel == '1':
            self.generate_rapel()

    def generate_date_approve_done_dummy(self):
        if self.date_start:
            date_start_obj = datetime.strptime(self.date_start, DATE_FORMAT)
            date_approve_obj = date_start_obj + timedelta(days=1)
            date_approve_str = date_approve_obj.strftime(DATETIME_FORMAT)
            self.date_approve = date_approve_str
            self.date_done = date_approve_str
            self.action_process()
            self.action_approve()
