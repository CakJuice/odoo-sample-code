# -*- coding: utf-8 -*-

from odoo import models, fields


class KaHrEmployeeKeluarga(models.Model):
    """Data employee family

    _name = 'ka_hr.employee.keluarga'
    """

    _name = 'ka_hr.employee.keluarga'
    _description = "SDM Hubungan Keluarga Pegawai"

    employee_id = fields.Many2one('hr.employee', string="Nama Karyawan", required=True)
    relation_type = fields.Selection([
        ('1', "Suami / Istri"),
        ('2', "Anak Kandung"),
        ('3', "Anak Angkat"),
        ('4', "Anak Tiri"),
        ('5', "Orang Tua"),
    ], string="Jenis", required=True)
    name_keluarga = fields.Char(string="Nama Keluarga", size=128, required=True)
    gender = fields.Selection([
        ('l', "Laki - Laki"),
        ('p', "Perempuan")
    ], string="Jenis Kelamin")
