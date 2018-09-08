# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrPayrollCompanyConfigWizard(models.TransientModel):
    """Wizard to configure `res.company` which related with this module.

    _name = 'ka_hr_payroll.company.config.wizard'
    """

    _name = 'ka_hr_payroll.company.config.wizard'

    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
                                 default=lambda self: self.env.user.company_id)
    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah",
                                        related='company_id.is_tunjangan_rumah')
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan",
                                          related='company_id.is_tunjangan_jabatan')
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus",
                                         related='company_id.is_tunjangan_khusus')
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi",
                                               related='company_id.is_tunjangan_representasi')

    thr_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah",
                                         related='company_id.thr_tunjangan_rumah')
    thr_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan",
                                           related='company_id.thr_tunjangan_jabatan')
    thr_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus",
                                          related='company_id.thr_tunjangan_khusus')
    thr_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi",
                                                related='company_id.thr_tunjangan_representasi')

    cuti_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah",
                                          related='company_id.cuti_tunjangan_rumah')
    cuti_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan",
                                            related='company_id.cuti_tunjangan_jabatan')
    cuti_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus",
                                           related='company_id.cuti_tunjangan_khusus')
    cuti_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi",
                                                 related='company_id.cuti_tunjangan_representasi')

    afkoop_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah",
                                            related='company_id.afkoop_tunjangan_rumah')
    afkoop_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan",
                                              related='company_id.afkoop_tunjangan_jabatan')
    afkoop_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus",
                                             related='company_id.afkoop_tunjangan_khusus')
    afkoop_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi",
                                                   related='company_id.afkoop_tunjangan_representasi')

    hr_notif_payroll = fields.Many2one('hr.employee', related='company_id.hr_notif_payroll',
                                       string="Notifikasi Tunj. Cuti")

    @api.multi
    def save_data(self):
        """To save data wizard. Called from button.

        Decorators:
            api.multi
        """
        self.company_id.is_tunjangan_rumah = self.is_tunjangan_rumah
        self.company_id.is_tunjangan_jabatan = self.is_tunjangan_jabatan
        self.company_id.is_tunjangan_khusus = self.is_tunjangan_khusus
        self.company_id.is_tunjangan_representasi = self.is_tunjangan_representasi

        self.company_id.thr_tunjangan_rumah = self.thr_tunjangan_rumah
        self.company_id.thr_tunjangan_jabatan = self.thr_tunjangan_jabatan
        self.company_id.thr_tunjangan_khusus = self.thr_tunjangan_khusus
        self.company_id.thr_tunjangan_representasi = self.thr_tunjangan_representasi

        self.company_id.cuti_tunjangan_rumah = self.cuti_tunjangan_rumah
        self.company_id.cuti_tunjangan_jabatan = self.cuti_tunjangan_jabatan
        self.company_id.cuti_tunjangan_khusus = self.cuti_tunjangan_khusus
        self.company_id.cuti_tunjangan_representasi = self.cuti_tunjangan_representasi

        self.company_id.afkoop_tunjangan_rumah = self.afkoop_tunjangan_rumah
        self.company_id.afkoop_tunjangan_jabatan = self.afkoop_tunjangan_jabatan
        self.company_id.afkoop_tunjangan_khusus = self.afkoop_tunjangan_khusus
        self.company_id.afkoop_tunjangan_representasi = self.afkoop_tunjangan_representasi

        self.company_id.hr_notif_payroll = self.hr_notif_payroll
