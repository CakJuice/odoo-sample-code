# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class KaHrPayrollCompanyPeriodicPromote(models.Model):
    """To create periodic promote based on company.

    _name = 'ka_hr_payroll.company.periodic.promote'
    """

    _name = 'ka_hr_payroll.company.periodic.promote'
    _order = 'date_start desc'
    _inherit = 'mail.thread'

    name = fields.Char(string="Nama", size=225)
    date_start = fields.Date(string="Tanggal Mulai", required=True, readonly=True,
                             default=fields.Date.today, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string="Unit/PG", required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('rapel', "Rapel Belum Diproses"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan"),
    ], string="Status", default='draft', required=True, track_visibility='onchange')
    date_approve = fields.Datetime(string="Tanggal Disetujui",
                                   states={'done': [('readonly', True)], 'canceled': [('readonly', True)]})
    date_done = fields.Datetime(string="Tanggal Berlaku",
                                states={'done': [('readonly', True)], 'canceled': [('readonly', True)]})
    no_sk = fields.Char(string="Nomor SK", size=24)
    notes = fields.Text(string="Catatan Persetujuan")
    state_rapel = fields.Selection([
        ('0', "Tidak Ada Rapel"),
        ('1', "Rapel Belum Diproses"),
        ('2', "Rapel Sudah Diproses"),
    ], string="Status Rapel", default='0', required=True, readonly=True)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         default=lambda self: self.env.user.company_id,
                                         states={'draft': [('readonly', False)]})
    promote_employee_ids = fields.One2many('ka_hr_payroll.company.periodic.promote.employee', 'periodic_id')

    @api.model
    def create(self, vals):
        """Override method `create()`. Use for insert data.

        Decorators:
			api.model

        Arguments:
            vals {Dict} -- Values insert data.

        Returns:
			Recordset -- Create result will return recordset.
        """
        record = super(KaHrPayrollCompanyPeriodicPromote, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            record.name = "Kenaikan Berkala Karyawan Staf {0}".format(record.company_id.name)
        return record

    @api.multi
    def write(self, vals):
        """Override method `write()`. Use for insert data.

        Decorators:
			api.multi

        Arguments:
            vals {Dict} -- Values update data.

        Returns:
			Recordset -- Write result will return recordset.
        """
        is_update = False
        vals_promote = {}
        if 'no_sk' in vals:
            is_update = True
            vals_promote['no_sk'] = vals.get('no_sk')
        if 'notes' in vals:
            is_update = True
            vals_promote['notes'] = vals.get('notes')
        if 'date_approve' in vals:
            is_update = True
            vals_promote['date_approve'] = vals.get('date_approve')
        if 'date_done' in vals:
            is_update = True
            vals_promote['date_done'] = vals.get('date_done')
        if is_update:
            for promote in self.promote_employee_ids:
                promote.write_promote_id(vals_promote)

        return super(KaHrPayrollCompanyPeriodicPromote, self).write(vals)

    @api.multi
    def unlink(self):
        """Override method `unlink()`. Use for insert data.

        Decorators:
			api.multi

        Returns:
			Recordset -- Unlink result will return recordset.
        """
        for promote in self.promote_employee_ids:
            promote.promote_id.unlink()
        return super(KaHrPayrollCompanyPeriodicPromote, self).unlink()

    @api.multi
    def action_draft(self):
        """Set state to `draft`.

        Decorators:
            api.multi
        """
        self.state = 'draft'
        for promote in self.promote_employee_ids:
            promote.action_draft()

    @api.multi
    def action_process(self):
        """Set state to `processed` then generate lines.

        Decorators:
            api.multi
        """
        for promote in self.promote_employee_ids:
            promote.action_process()
        self.state = 'processed'

    def _check_rapel(self):
        """To check this scale is must have rapel or not.
        """
        date_approve = datetime.strptime(self.date_approve, DATETIME_FORMAT)
        date_start = datetime.strptime(self.date_start, DATE_FORMAT)

        if date_approve.month != date_start.month or date_approve.year != date_start.year:
            return True
        elif date_approve.month == date_start.month and date_approve.year == date_start.year:
            config = self.env['ka_hr_payroll.config'].default_config()
            if date_approve.day > config.date_end:
                return True
        return False

    @api.multi
    def action_approve(self):
        """Check rapel and set state to `rapel` or `done`.

        Decorators:
            api.multi
        """
        if not self.date_approve:
            self.date_approve = fields.Datetime.now()
        for promote in self.promote_employee_ids:
            promote.date_approve = self.date_approve
            promote.action_approve()
        if self._check_rapel():
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

    @api.multi
    def action_done(self):
        """Generate rapel then set `state` to `done` and `date_done` to date now.

        Decorators:
            api.multi
        """
        if not self.date_done:
            self.date_done = fields.Datetime.now()
        if self.state == 'rapel':
            for promote in self.promote_employee_ids:
                promote.date_done = self.date_done
                promote.action_done()
            self.state_rapel = '2'
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        """Set `state='canceled'`.
        """
        self.state = 'canceled'
        for promote in self.promote_employee_ids:
            promote.action_cancel()


class KaHrPayrollCompanyPeriodicPromoteEmployee(models.Model):
    """Data employee of periodic promote.

    _name = 'ka_hr_payroll.company.periodic.promote.employee'
    """

    _name = 'ka_hr_payroll.company.periodic.promote.employee'

    periodic_id = fields.Many2one('ka_hr_payroll.company.periodic.promote', string="Promosi Berkala",
                                  required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string="Karyawan", required=True)
    new_golongan_id = fields.Many2one('hr.golongan', string="Golongan Baru", required=True)
    new_scale = fields.Float(string="Skala Baru", digits=(6, 3), required=True)
    # new_japres = fields.Float(string="Japres Baru", digits=(5, 2), required=True)
    promote_id = fields.Many2one('hr.employee.promote', string="Ref. Histori Promosi", readonly=True)
    old_promote_id = fields.Many2one('hr.employee.promote', compute='_compute_old_promote',
                                     string="Ref. Data Lama")
    old_department_id = fields.Many2one('hr.department', compute='_compute_old_promote',
                                        string="Divisis Lama")
    old_jabatan_id = fields.Many2one('hr.jabatan', compute='_compute_old_promote',
                                     string="Jabatan Lama")
    old_pangkat_id = fields.Many2one('hr.pangkat', compute='_compute_old_promote',
                                     string="Pangkat Terakhir")
    old_golongan_id = fields.Many2one('hr.golongan', compute='_compute_old_promote',
                                      string="Golongan Terakhir")
    old_status_id = fields.Many2one('hr.status', compute='_compute_old_promote',
                                    string="Status Terakhir")
    old_scale = fields.Float(string="Skala Lama", digits=(6, 3), compute='_compute_old_promote')
    # old_japres = fields.Float(string="Jasa Prestasi Lama", digits=(5, 2), compute='_compute_old_promote')
    old_company_id = fields.Many2one('res.company', compute='_compute_old_promote',
                                     string="Unit/PG Terakhir")

    @api.depends('employee_id')
    def _compute_old_promote(self):
        """Computing old last promote.
        """
        for promote in self:
            if promote.old_promote_id:
                # data sudah ada
                continue

            last_promote = self.env['hr.employee.promote'].get_last_processed_promote(promote.employee_id.id)
            if last_promote:
                if last_promote.id == promote.id:
                    continue

                promote.old_promote_id = last_promote
                promote.old_department_id = last_promote.department_id
                promote.old_jabatan_id = last_promote.jabatan_id
                promote.old_pangkat_id = last_promote.pangkat_id
                promote.old_golongan_id = last_promote.golongan_id
                promote.old_status_id = last_promote.status_id
                promote.old_company_id = last_promote.company_id
                promote.old_scale = last_promote.scale
                # promote.old_japres = last_promote.japres

    def generate_promote(self):
        """To generate `hr.employee.promote` based from this record.
        """
        data_promote = {
            'date_start': self.periodic_id.date_start,
            'no_sk': self.periodic_id.no_sk,
            'date_approve': self.periodic_id.date_approve,
            'date_done': self.periodic_id.date_done,
            'employee_id': self.employee_id.id,
            'department_id': self.old_department_id.id,
            'jabatan_id': self.old_jabatan_id.id,
            'pangkat_id': self.old_pangkat_id.id,
            'golongan_id': self.new_golongan_id.id,
            'status_id': self.old_status_id.id,
            'company_id': self.old_company_id.id,
            'scale': self.new_scale,
            # 'japres': self.new_japres,
            'promote_type': '2',
            'periodic_promote_id': self.id,
        }

        promote = self.env['hr.employee.promote'].create(data_promote)
        self.promote_id = promote

    def action_draft(self):
        """Set state `promote_id` to `draft`.
        """
        if self.promote_id:
            self.promote_id.action_draft()

    def action_process(self):
        """Set state `promote_id` to `processed` then generate lines.
        """
        self.generate_promote()
        if self.promote_id:
            self.promote_id.action_process()

    def action_approve(self):
        """Check rapel and set state `promote_id` to `rapel` or `done`.
        """
        if self.promote_id:
            self.promote_id.action_approve()

    def action_rapel(self):
        """Set state `promote_id` to `rapel` and `state_rapel` to `2`.
        """
        if self.promote_id:
            self.promote_id.action_rapel()

    def action_done(self):
        """Generate `promote_id` rapel then set `state` to `done` and `date_done` to date now.
        """
        if self.promote_id:
            self.promote_id.action_done()

    def action_cancel(self):
        """Set state `promote_id` to `canceled`.
        """
        if self.promote_id:
            self.promote_id.action_cancel()

    def write_promote_id(self, vals):
        """Write `promote_id` based on `periodic_id` values.

        Arguments:
            vals {Dict} -- Values update data.

        Returns:
            Recordset -- Unlink result will return recordset.
        """
        return self.promote_id.write(vals)
