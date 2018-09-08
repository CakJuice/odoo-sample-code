# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrPayrollStatus(models.Model):
    """Data status of employee

    _inherit = 'hr.status'
    """

    _inherit = 'hr.status'

    is_default_payroll = fields.Boolean(string="Gaji Ditetapkan", default=False)
    is_multiply_konjungtur = fields.Boolean(string="Dikalikan Konjungtur", default=False,
                                            help="Apakah gaji pokok dikalikan dengan konjungtur?")
    is_daily_pay = fields.Boolean(string="Pembayaran Harian", default=False,
                                  help="Apakah gaji dibayarkan harian?")
    is_gaji_proportion = fields.Boolean(string="Proporsi < 1 Bulan", default=False)
    is_thr = fields.Boolean(string="Dapat THR", default=True)
    thr_multiply = fields.Float(string="Index THR", digits=(5, 2), default=1.00)
    is_tunjangan_cuti = fields.Boolean(string="Dapat Tunj. Cuti", default=True)
    cuti_multiply = fields.Float(string="Index Tunj. Cuti", digits=(5, 2), default=1.00)

    @api.multi
    def write(self, vals):
        # Cek data potongan semua karyawan, samakan dengan is_multiply_konjungtur
        if 'is_multiply_konjungtur' in vals:
            employees = self.env['hr.employee'].search([
                ('status_id', '=', self.id),
            ])

            for employee in employees:
                for potongan in employee.potongan_ids:
                    potongan.is_multiply_konjungtur = vals.get('is_multiply_konjungtur')

        return super(KaHrPayrollStatus, self).write(vals)

    def check_status_member(self, operator, status_id, status_compare_id):
        """To check some status is member of this status or not.

        Arguments:
            operator {String} -- Operator of check member, it can be 'parent_of' or 'child_of'.
            status_id {Int} -- ID of `hr.status` which search members.
            status_compare_id {Int} -- ID of `hr.status`.

        Returns:
            Boolean -- If `status_compare_id` in members it will return True. Vice versa.
        """
        members = self.search([
            ('id', operator, status_id)
        ])
        for member in members:
            if member.id == status_compare_id:
                return True
        return False
