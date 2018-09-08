# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api

class KaHrEmployeeCreateWizard(models.TransientModel):
    _name = 'hr.employee.create.wizard'

    name = fields.Char(string="Nama", size=255, required=True)
    nik = fields.Char(string="N.I.K", size=10, required=True)
    tgl_masuk = fields.Date(string="Tanggal Masuk", required=True, default=fields.Date.today)
    department_id = fields.Many2one('hr.department', string="Departemen")
    jabatan_id = fields.Many2one('hr.jabatan', string="Jabatan")
    pangkat_id = fields.Many2one('hr.pangkat', string="Pangkat")
    golongan_id = fields.Many2one('hr.golongan', string="Golongan")
    status_id = fields.Many2one('hr.status', string="Status", required=True)
    company_id = fields.Many2one('res.company', string="Unit/PG", required=True)
    no_sk = fields.Char(string="Nomor SK", size=24)
    notes = fields.Text(string="Catatan Persetujuan")

    @api.onchange('department_id')
    def _onchange_department(self):
        self.company_id = None
        if self.department_id:
            self.company_id = self.department_id.company_id

    @api.multi
    def save_data(self):
        """To save data in `hr.employee` & `hr.employee.promote` model.

		Decorators:
			api.multi
		"""
        data_employee = {
            'name': self.name,
            'nik': self.nik,
            'tgl_masuk': self.tgl_masuk,
        }
        employee = self.env['hr.employee'].create(data_employee)
        data_promote = {
            'date_start': self.tgl_masuk,
            'promote_type': '4',
            'employee_id': employee.id,
            'status_id': self.status_id.id,
            'company_id': self.company_id.id,
        }

        if self.department_id:
            data_promote['department_id'] = self.department_id.id
        if self.jabatan_id:
            data_promote['jabatan_id'] = self.jabatan_id.id
        if self.pangkat_id:
            data_promote['pangkat_id'] = self.pangkat_id.id
        if self.golongan_id:
            data_promote['golongan_id'] = self.golongan_id.id
        if self.no_sk:
            data_promote['no_sk'] = self.no_sk
        if self.notes:
            data_promote['notes'] = self.notes

        promote = self.env['hr.employee.promote'].create(data_promote)
        promote.date_approve = self.tgl_masuk
        promote.date_done = self.tgl_masuk
        promote.action_process()
        promote.action_approve()
        self.env.user.notify_info("Data karyawan baru berhasil dibuat!")
