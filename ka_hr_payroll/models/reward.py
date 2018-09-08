# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrPayrollReward(models.Model):
    """Data of payroll reward.

    _name = 'ka_hr_payroll.reward'
    """

    _name = 'ka_hr_payroll.reward'

    REWARD_TYPE_NAME = [
        ('1', "Penghargaan Masa Dinas"),
        ('2', "Penghargaan Pisah Pensiun")
    ]

    name = fields.Char(string="Nama Penghargaan", size=255)
    code = fields.Char(string="Kode", size=3, required=True)
    year_period = fields.Integer(string="Tahun Periode", required=True)
    reward_type = fields.Selection(REWARD_TYPE_NAME, string="Tipe Penghargaan", default='1', required=True)
    multiply_value = fields.Float(string="Nilai Pengali", required=True)
    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", default=False)
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", default=False)
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", default=False)
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", default=False)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True,
                                         default=lambda self: self.env.user.company_id)

    def _get_type_name(self, key):
        """To get type name of `scale_type` value.

        Arguments:
            key {String} -- `scale_type` value.

        Returns:
            String -- Result of `scale_type` value check.
        """
        for _type in self.REWARD_TYPE_NAME:
            if _type[0] == key:
                return _type[1]
        return ''

    @api.model
    def create(self, vals):
        """Override method `create()`. Use for insert data

        Decorators:
			api.model

        Arguments:
            vals {Dict} -- Values insert data

        Returns:
			Recordset -- Create result will return recordset
        """
        record = super(KaHrPayrollReward, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            type_name = self._get_type_name(record.reward_type)
            record.name = "{0} {1} Tahun, {2}".format(type_name, record.year_period, record.company_payroll_id.name)
        return record
