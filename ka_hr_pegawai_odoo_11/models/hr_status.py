# -*- coding: utf-8 -*-

from odoo import models, fields, api


class KaHrStatus(models.Model):
    """Master data of employee status.

    _name = 'hr.status'
    """

    _name = 'hr.status'

    code = fields.Char(string="Kode", size=6, required=True)
    name = fields.Char(string="Nama Status", size=64, required=True)
    parent_id = fields.Many2one('hr.status', string="Parent")
    child_ids = fields.One2many('hr.status', 'parent_id', string="Childs")

    _sql_constraints = [
        ('hr_status_unique', 'UNIQUE(code)', "Kode sudah digunakan. Silakan gunakan kode lain.")
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
