# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields, api


class KaHrPayrollEmployeeHolidays(models.Model):
    """Data holidays of employee.

    _inherit = 'hr.holidays'
    """

    _inherit = 'hr.holidays'

    tunjangan_holiday_id = fields.Many2one('ka_hr_payroll.tunjangan.holidays', string="Ref. Tunjangan",
                                           readonly=True)

    @api.multi
    def get_dinas_cost(self):
        if self.holiday_status_help != 'dinas':
            return

        dinas_cost = self.env['ka_hr_payroll.employee.dinas'].search([
            ('holiday_id', '=', self.id),
        ], limit=1)

        view_id = self.env.ref('ka_hr_payroll.view_employee_dinas_form').id
        action = self.env.ref('ka_hr_payroll.action_employee_dinas')
        result = action.read()[0]
        result['views'] = [(view_id, 'form')]
        result['view_id'] = view_id
        result['domain'] = [('holiday_id', '=', self.id)]
        result['context'] = {
            'default_holiday_id': self.id,
        }

        if dinas_cost:
            result['res_id'] = dinas_cost.id

        return result
