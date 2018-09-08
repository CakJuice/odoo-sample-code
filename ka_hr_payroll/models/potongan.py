# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class KaHrPayrollPotongan(models.Model):
    """Master data of employee deduction (Potongan Karyawan).

    _name = 'ka_hr_payroll.potongan'
    """

    _name = 'ka_hr_payroll.potongan'

    code = fields.Char(string="Kode", size=3, required=True)
    name = fields.Char(string="Nama Potongan", size=64, required=True)
    is_mandatory = fields.Boolean(string="Potongan Wajib", default=True)
    authority = fields.Selection([
        ('1', "SDM"),
        ('2', "TUK"),
    ], string="Wewenang", default='1', required=True)
    type_potongan = fields.Selection([
        ('1', "Prosentase"),
        ('2', "Potongan Tetap"),
        ('3', "Potongan Manual"),
    ], string="Tipe Potongan", default='1', required=True)
    prosentase = fields.Float(string="Prosentase (%)", digits=(5, 2))
    fixed_value = fields.Float(string="Nilai Potongan Tetap")
    is_max_value = fields.Boolean(string="Gunakan Nilai Maks. Potongan", default=False)
    max_value = fields.Float(string="Nilai Maks. Potongan")
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian",
                                         default=lambda self: self.env.user.company_id, required=True)
    employee_ids = fields.One2many('ka_hr_payroll.potongan.employee', 'potongan_id', string="Data Karyawan")

    _sql_constraints = [
        ('payroll_potongan_unique', 'UNIQUE(code, company_payroll_id)',
         "Kode sudah digunakan! Silakan gunakan kode lain.")
    ]

    @api.onchange('type_potongan')
    def _onchange_type_potongan(self):
        self.prosentase = None
        self.fixed_value = None
        self.is_max_value = False

    @api.onchange('is_max_value')
    def _onchange_is_max_value(self):
        self.max_value = None

    def generate_dummy(self):
        data_status = [
            {'code': '02', 'is_default_payroll': False, 'is_multiply_konjungtur': True},
            {'code': '03', 'is_default_payroll': True, 'is_multiply_konjungtur': False}
        ]

        for ds in data_status:
            status = self.env['hr.status'].search([('code', '=', ds.get('code'))], limit=1)
            if status:
                status.is_default_payroll = ds.get('is_default_payroll')
                status.is_multiply_konjungtur = ds.get('is_multiply_konjungtur')
        self._cr.commit()

        # data_potongan = [
        #     {'code': '01', 'name': "BPJS Ktngakerjaan JHT", 'prosentase': 2.00},
        #     {'code': '02', 'name': "YKKA", 'prosentase': 2.60},
        #     {'code': '03', 'name': "BPJS Pensiun", 'prosentase': 3.00,
        #         'is_max_value': True,
        #         'max_value': 242820},
        #     {'code': '04', 'name': "BPJS Kesehatan", 'prosentase': 5.00,
        #         'is_max_value': True,
        #         'max_value': 236250},
        #     {'code': '05', 'name': "DAPEN KA", 'prosentase': 5.00},
        #     {'code': '06', 'name': "DAPEN BRI", 'prosentase': 5.00},
        # ]

        company = self.env['res.company'].search([('code', '=', '1')], limit=1)
        # for data in data_potongan:
        #     data['company_payroll_id'] = company.id
        #     self.create(data)

        hr_config = self.env['hr.config'].default_config()
        employees = self.env['hr.employee'].search([
            ('pensiun', '=', False),
            ('status_id', 'child_of', hr_config.hr_status_staf_id.id),
            ('company_payroll_id', '=', company.id)
        ])

        potongan = self.search([])

        threshold = datetime.strptime('2013-01-01', DATE_FORMAT)
        for employee in employees:
            if not employee.tgl_masuk:
                employee.tgl_masuk = '2010-01-01'
            tgl_masuk = datetime.strptime(employee.tgl_masuk, DATE_FORMAT)
            for p in potongan:
                if p.code == '02' and employee.status_id.code == '09':
                    continue

                if p.code == '05':
                    if tgl_masuk >= threshold:
                        continue

                if p.code == '06':
                    if tgl_masuk < threshold:
                        continue

                konjungtur_type = '2' if p.code == '05' or p.code == '06' else '1'

                is_multiply_konjungtur = employee.status_id.is_multiply_konjungtur
                self.env['ka_hr_payroll.potongan.employee'].create({
                    'potongan_id': p.id,
                    'employee_id': employee.id,
                    'is_multiply_konjungtur': is_multiply_konjungtur,
                    'konjungtur_type': konjungtur_type,
                })


class KaHrPayrollPotonganEmployee(models.Model):
    """List of `hr.employee` member of `ka_hr_payroll.potongan`.

    _name = 'ka_hr_payroll.potongan.employee'
    """

    _name = 'ka_hr_payroll.potongan.employee'

    _KONJUNGTUR_TYPE_NAME = [
        ('1', "Konjungtur Gaji"),
        ('2', "Konjungtur Dapen"),
    ]

    potongan_id = fields.Many2one('ka_hr_payroll.potongan', string="Potongan", required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string="Karyawan", required=True)
    is_multiply_konjungtur = fields.Boolean(string="Dikalikan Konjungtur", compute='_compute_konjungtur',
                                            store=True)
    konjungtur_type = fields.Selection(_KONJUNGTUR_TYPE_NAME, string="Tipe")

    @api.constrains('is_multiply_konjungtur')
    def _check_validity(self):
        for line in self:
            if line.is_multiply_konjungtur and not line.konjungtur_type:
                raise ValidationError("Tipe konjungtur harus diisi.")

    @api.depends('employee_id', 'potongan_id')
    def _compute_konjungtur(self):
        for line in self:
            line.is_multiply_konjungtur = line.employee_id.status_id.is_multiply_konjungtur
