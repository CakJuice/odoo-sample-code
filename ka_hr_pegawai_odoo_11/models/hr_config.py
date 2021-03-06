# -*- coding: utf-8 -*-

from odoo import models, fields


class KaHrConfig(models.Model):
    """Setting for `hr` modules, which call in `ka_hr_pegawai.config.wizard`.
    This model just only have 1 record for config, so the `ka_hr_pegawai.config.wizard` only call first record.

    _name = 'hr.config'
    """

    _name = 'hr.config'

    DEFAULT_PENSIUN_AGE = 55
    DEFAULT_MPP_MONTH = 4

    hr_status_direksi_id = fields.Many2one('hr.status', string="Status Direksi",
                                           help="Pilih status untuk 'Direksi'.")
    hr_status_staf_id = fields.Many2one('hr.status', string="Status Staf",
                                        help="Pilih status untuk 'Staf'.")
    hr_status_pelaksana_id = fields.Many2one('hr.status', string="Status Pelaksana",
                                             help="Pilih status untuk 'Pelaksana'.")
    hr_pensiun_age = fields.Integer(string="Usia Pensiun", default=DEFAULT_PENSIUN_AGE,
                                    help="Untuk menentukan pensiun dari karyawan.")
    hr_mpp_month = fields.Integer(string="Bulan MPP", default=DEFAULT_MPP_MONTH,
                                  help="Untuk menentukan jumlah bulan MPP sebelum pensiun.")

    def default_config(self):
        """To get default config. Querying for first record only.

        Returns:
            Recordset -- Result default config
        """
        config = self.search([], limit=1, order='id desc')
        if not config:
            config = self.create({
                'hr_pensiun_age': self.DEFAULT_PENSIUN_AGE,
                'hr_mpp_month': self.DEFAULT_MPP_MONTH,
            })
            self._cr.commit()
        return config
