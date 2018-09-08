# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrPayrollConfigWizard(models.TransientModel):
    """Wizard to configure models which related with this module.

    _name = 'ka_hr_payroll.config.wizard'
    """

    _name = 'ka_hr_payroll.config.wizard'

    _DEFAULT_DATE_START = 21
    _DEFAULT_DATE_END = 20
    _DATE_LIST = [(val, str(val)) for val in range(1, 32)]

    def default_config(self):
        """To get default config from `ka_hr_payroll.config` model.

        Returns:
            Recordset -- Result default config
        """
        return self.env['ka_hr_payroll.config'].default_config()

    config_id = fields.Many2one('ka_hr_payroll.config', string="Config", default=default_config)
    date_start = fields.Selection(_DATE_LIST, related='config_id.date_start', string="Tanggal Mulai Penggajian",
                                  required=True, default=_DEFAULT_DATE_START)
    date_end = fields.Selection(_DATE_LIST, related='config_id.date_end', string="Tanggal Akhir Penggajian",
                                required=True, default=_DEFAULT_DATE_END)
    # is_gaji_proportion = fields.Boolean(string="Proporsi < 1 Bulan", default=True)
    min_month_thr_full = fields.Integer(string="Min. THR Penuh (Bulan)", required=True, default=12)
    min_month_thr_proportion = fields.Integer(string="Min. THR Proporsional (Bulan)", required=True, default=1)
    month_thr_proportion_value = fields.Integer(string="Nilai Pembagi Proporsi", required=True, default=12)

    @api.multi
    def save_data(self):
        """To save data wizard. Called from button.

        Decorators:
            api.multi
        """
        self.config_id.date_start = self.date_start
        self.config_id.date_end = self.date_end
        # self.config_id.is_gaji_proportion = self.is_gaji_proportion
        self.config_id.min_month_thr_proportion = self.min_month_thr_proportion
        self.config_id.min_month_thr_full = self.min_month_thr_full
        self.config_id.month_thr_proportion_value = self.month_thr_proportion_value
