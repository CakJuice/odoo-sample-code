# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrGolongan(models.Model):
    """Master data of employee job group (golongan).

    _name = 'hr.golongan'
    """

    _name = 'hr.golongan'
    _description = "SDM master data golongan karyawan"
    _order = 'name asc'

    name = fields.Char(string="Nama", size=12, required=True)
    # employee_ids = fields.One2many('hr.employee', 'golongan_id', string="Karyawan", readonly=True)
