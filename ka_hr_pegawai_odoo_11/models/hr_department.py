# -*- coding: utf-8 -*-

from odoo import models, fields


class KaHrDepartment(models.Model):
    _inherit = 'hr.department'

    code = fields.Char(string="Kode", size=4)
