# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from ..util_helpers import is_ip_server

_logger = logging.getLogger(__name__)


class KaHrEmployee(models.Model):
    """Master data of employee.

    _inherit = 'hr.employee'
    """

    _inherit = 'hr.employee'

    nik = fields.Char(string='N I K', size=10, required=True)
    # position = fields.Char(string="Posisi", compute="_complite_position")
    address = fields.Char(string='Alamat', size=64)
    address_city = fields.Char(string='Kota', size=32)
    tgl_masuk = fields.Date(string='Tgl. Masuk', readonly=True)
    home_phone = fields.Char(string='Telepon Rumah', size=16)
    npwp = fields.Char(string='NPWP', size=32)
    bank_id = fields.Many2one('res.bank', string='Bank')
    acc_number = fields.Char(string='No. Rekening', size=32)
    acc_name = fields.Char(string='Atas Nama', size=32)
    place_birthday = fields.Char(string='Kelahiran', size=32)
    graduate_ids = fields.One2many('hr.employee.graduate', 'employee_id', string='Pendidikan Formal')
    course_ids = fields.One2many('hr.employee.course', 'employee_id', string=' Pendidikan Non Formal')
    pensiun = fields.Boolean(string="Berhenti", default=False)
    stop_type = fields.Selection([
        ('6', "Pensiun"),
        ('7', "Pengunduran Diri"),
        ('8', "Pemecatan"),
        ('9', "Meninggal Dunia"),
        ('10', "Kontrak Selesai"),
    ], string="Tipe Berhenti")
    religion = fields.Selection([
        ('islam', 'Islam'),
        ('kristen', 'Kristen'),
        ('katolik', 'Katolik'),
        ('hindu', 'Hindu'),
        ('budha', 'Budha'),
        ('lain', 'Lain-nya'),
    ], 'Agama')

    is_tetap = fields.Boolean(string="Pegawai Tetap")
    tgl_tetap = fields.Date(string="Tanggal Pengangkatan", help="Tanggal pengangkatan sebagai pegawai tetap.")
    tgl_pensiun = fields.Date(string="Tanggal Pensiun", help="Tanggal pensiun pegawai.")
    tgl_mpp = fields.Date(string="Tanggal MPP", help="Tanggal persiapan pensiun pegawai.")
    tgl_cuti = fields.Date(string="Tanggal Hak Cuti",
                           help="Tanggal munculnya hak cuti tahunan ataupun cuti besar.")
    is_contract = fields.Boolean(string="Kontrak")
    date_contract_start = fields.Date(string="Tanggal Mulai Kontrak")
    date_contract_end = fields.Date(string="Tanggal Akhir Kontrak")

    company_id = fields.Many2one('res.company', string="Unit/PG", readonly=True)
    department_id = fields.Many2one('hr.department', string="Divisi", readonly=True)
    jabatan_id = fields.Many2one('hr.jabatan', string="Jabatan", readonly=True)
    pangkat_id = fields.Many2one('hr.pangkat', string="Pangkat", readonly=True)
    golongan_id = fields.Many2one('hr.golongan', string="Golongan", readonly=True)
    status_id = fields.Many2one('hr.status', string="Status", readonly=True)
    last_processed_promote = fields.Many2one('hr.employee.promote', compute='_compute_processed_promote')
    history_aksw = fields.Text(string="Histori AKSW")

    kpi_score = fields.Float(string="Skor KPI", default=0.0)

    employee_keluarga_ids = fields.One2many('ka_hr.employee.keluarga', 'employee_id')

    is_user = fields.Boolean(string="Is Current User", compute='_compute_user')
    is_officer = fields.Boolean(string="Is Officer", compute='_compute_user')

    @api.multi
    def _compute_user(self):
        for employee in self:
            user = self.env.user
            employee.is_user = user == employee.user_id
            employee.is_officer = user.has_group('hr.group_hr_user')

    # Override
    @api.onchange('user_id')
    def _onchange_user(self):
        pass

    @api.multi
    def _compute_processed_promote(self):
        for employee in self:
            employee.last_processed_promote = self.env['hr.employee.promote'].get_last_processed_promote(employee.id)

    @api.onchange('birthday')
    def _onchange_birthday(self):
        """Compute tgl_mpp & tgl_pensiun, based on birthday

        Decorators:
            api.depends('birthday')
        """
        config = self.env['hr.config'].default_config()
        for s in self:
            # if not s.company_id.hr_pensiun_age or not s.company_id.hr_mpp_month:
            # 	continue
            if not config.hr_pensiun_age or not config.hr_mpp_month:
                continue

            if s.birthday:
                birthday_obj = datetime.strptime(s.birthday, DATE_FORMAT)
                pensiun_obj = birthday_obj + relativedelta(years=config.hr_pensiun_age)
                pensiun_year = pensiun_obj.year
                pensiun_month = pensiun_obj.month
                pensiun_new = pensiun_obj
                if pensiun_obj.day > 1:
                    if pensiun_obj.month >= 12:
                        pensiun_month = 1
                        pensiun_year += 1
                    else:
                        pensiun_month += 1
                    pensiun_new = datetime.strptime('{}-{}-{}'.format(pensiun_year, pensiun_month, 1), DATE_FORMAT)

                s.tgl_pensiun = pensiun_new

                mpp_month = pensiun_month
                mpp_year = pensiun_year
                if pensiun_month <= config.hr_mpp_month:
                    mpp_month = (12 + pensiun_month)
                    mpp_year -= 1
                mpp_month -= config.hr_mpp_month

                s.tgl_mpp = datetime.strptime('{}-{}-{}'.format(mpp_year, mpp_month, 1), DATE_FORMAT)
            else:
                s.tgl_pensiun = None

    @api.multi
    def action_view_sp(self):
        """To open view SP.

        Decorators:
            api.multi

        Returns:
            Dict -- Result of view action
        """
        action = self.env.ref('ka_hr_pegawai.action_employee_sp')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id), ('state', '!=', 'draft')]
        result['context'] = {
            'default_employee_id': self.id
        }
        return result

    @api.multi
    def action_jabatan(self):
        """To view all `hr.employee.jabatan` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        action = self.env.ref('ka_hr_pegawai.action_employee_jabatan')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result

    @api.multi
    def action_pangkat(self):
        """To view all `hr.employee.pangkat` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        action = self.env.ref('ka_hr_pegawai.action_employee_pangkat')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result

    @api.multi
    def action_golongan(self):
        """To view all `hr.employee.golongan` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        action = self.env.ref('ka_hr_pegawai.action_employee_golongan')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result

    @api.multi
    def action_status(self):
        """To view all `hr.employee.status` related with this model.

        Returns:
            Dict -- Result of action view.
        """
        action = self.env.ref('ka_hr_pegawai.action_employee_status')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result

    @api.multi
    def action_view_promote(self):
        action = self.env.ref('ka_hr_pegawai.action_employee_promote')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result

    def check_employee_contract_end(self):
        """Check employee who's end of contract.
        """
        employees = self.env['hr.employee'].search([
            ('pensiun', '=', False),
            ('is_contract', '=', True),
            ('date_contract_end', '=', fields.Date.today())
        ])

        for employee in employees:
            employee.pensiun = True
            employee.stop_type = '10'
            employee.is_contract = False

    @api.model
    def cron_check_daily(self):
        """Cron check employee daily.
        """
        if not is_ip_server():
            return
        _logger.info('===================== Check employee contract end =====================')
        self.check_employee_contract_end()

    def action_open_employee(self):
        print(self)
        action = self.env.ref('ka_hr_pegawai.action_open_employee')
        result = action.read()[0]
        if self.env.user.has_group('hr.group_hr_user'):
            return result

        result['domain'] = [
            ('pensiun', '=', False),
            ('user_id', '=', self.env.user.id)
        ]
        return result
