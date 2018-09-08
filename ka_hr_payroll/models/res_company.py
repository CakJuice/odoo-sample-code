# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrPayrollCompanyConfig(models.Model):
    """Setting `res.company` related with payroll.

    _inherit = 'res.company'
    """

    _inherit = 'res.company'

    is_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", default=True)
    is_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", default=True)
    is_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", default=True)
    is_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", default=True)
    konjungtur_gaji = fields.Float(string="Konjungtur Gaji (%)", compute='_compute_konjungtur')
    konjungtur_dapen = fields.Float(string="Konjungtur Dapen (%)", compute='_compute_konjungtur')

    thr_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", default=False)
    thr_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", default=False)
    thr_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", default=False)
    thr_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", default=False)

    cuti_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", default=False)
    cuti_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", default=False)
    cuti_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", default=False)
    cuti_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", default=False)

    afkoop_tunjangan_rumah = fields.Boolean(string="Tunj. Rumah", default=False)
    afkoop_tunjangan_jabatan = fields.Boolean(string="Tunj. Jabatan", default=False)
    afkoop_tunjangan_khusus = fields.Boolean(string="Tunj. Khusus", default=False)
    afkoop_tunjangan_representasi = fields.Boolean(string="Tunj. Representasi", default=False)

    hr_notif_payroll = fields.Many2one('hr.employee', string="Notifikasi Tunj. Cuti")

    @api.multi
    def _compute_konjungtur(self):
        for company in self:
            company.konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                       company.id).value
            company.konjungtur_dapen = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('2',
                                                                                                        company.id).value
