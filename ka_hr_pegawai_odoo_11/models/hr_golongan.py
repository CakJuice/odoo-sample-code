# -*- coding: utf-8 -*-

from odoo import models, fields


class KaHrGolongan(models.Model):
    """Master data of employee job group (golongan).

    _name = 'hr.golongan'
    """

    _name = 'hr.golongan'
    _description = "SDM master data golongan karyawan"
    _order = 'name asc'

    name = fields.Char(string="Nama", size=12, required=True)
