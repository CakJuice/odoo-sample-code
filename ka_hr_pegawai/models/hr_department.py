# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrDepartment(models.Model):
    """Master data department of employee.

	_inherit = 'hr.employee'
	"""

    _inherit = 'hr.department'

    code = fields.Char(string="Kode", size=4)
