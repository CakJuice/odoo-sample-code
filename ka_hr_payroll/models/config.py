# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields


class KaHrPayrollConfig(models.Model):
    """Setting for `ka_hr_payroll` modules, which call in `ka_hr_payroll.config.wizard`.
	This model just only have 1 record for config, so the `ka_hr_payroll.config.wizard` only call first record.

	_name = 'ka_hr_payroll.config'
	"""

    _name = 'ka_hr_payroll.config'
    _order = 'date_start desc'

    _DEFAULT_DATE_START = 21
    _DEFAULT_DATE_END = 20
    _DATE_LIST = [(val, str(val)) for val in range(1, 32)]

    date_start = fields.Selection(_DATE_LIST, string="Tanggal Mulai Penggajian", required=True,
                                  default=_DEFAULT_DATE_START)
    date_end = fields.Selection(_DATE_LIST, string="Tanggal Akhir Penggajian", required=True,
                                default=_DEFAULT_DATE_END)
    # is_gaji_proportion = fields.Boolean(string="Proporsi < 1 Bulan", default=True)
    min_month_thr_full = fields.Integer(string="Min. THR Penuh", required=True, default=12)
    min_month_thr_proportion = fields.Integer(string="Min. THR Proporsional", required=True, default=1)
    month_thr_proportion_value = fields.Integer(string="Nilai Pembagi Proporsi", required=True, default=12)

    def default_config(self):
        """To get default config. Querying for first record only.

        Returns:
            Recordset -- Result default config
        """
        config = self.search([], limit=1, order='id desc')
        if not config:
            config = self.create({})
            self._cr.commit()
        return config
