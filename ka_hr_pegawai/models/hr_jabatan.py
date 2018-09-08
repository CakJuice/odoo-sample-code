# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrJabatan(models.Model):
    """Master data of employee job position (jabatan).
    Replacement of `hr.job`.

	_inherit = 'hr.jabatan'
    """

    _name = 'hr.jabatan'
    _order = 'code asc'

    code = fields.Char(string="Kode", size=6, required=True)
    name = fields.Char(string="Nama Jabatan", size=128, required=True)
    level = fields.Selection([
        (1, "I    - Direktur Utama"),
        (2, "II   - Direktur"),
        (3, "III  - Kepala Divisi"),
        (4, "IV   - Kepala Bagian"),
        (5, "V    - Kepala Seksi"),
        (6, "VI   - Kepala Sub Seksi"),
        (7, "VII  - Pelaksana"),
        # (8, "VIII - Pelaksana Harian"),
        # (9, "IX   - Pelaksana Kampanye")
    ], string="Level", required=True)
    # employee_ids = fields.One2many('hr.employee', 'jabatan_id', string="Karyawan", readonly=True)

    _sql_constraints = [
        ('hr_jabatan_unique', 'UNIQUE(code)', "Kode sudah digunakan! Silakan gunakan kode lain.")
    ]

    @api.multi
    def name_get(self):
        """Get representative name for this model.
        Override from method `name_get()`.

        Decorators:
            api.multi
        """
        res = []
        for record in self:
            code = record.code or ''
            name = record.name or ''
            res.append((record.id, '{0} - {1}'.format(code, name)))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        """To searching this model by representative name in method `name_get()`.
        Override from method `name_search()`.

        Decorators:
            api.model

        Keyword Arguments:
            name {String} -- Query string to search (default: {''})
            args {List} -- Added args for search query (default: {None})
            operator {String} -- Operator condition for search query (default: {'ilike'})
            limit {Int} -- Limit data search query (default: {80})
        """
        if not args:
            args = []

        if name:
            record = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
        else:
            record = self.search(args, limit=limit)

        return record.name_get()
