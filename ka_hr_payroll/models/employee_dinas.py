# -*- coding: utf-8 -*-

from __future__ import division

from odoo import models, fields, api

from ..helpers import format_local_currency


class KaHrPayrollEmployeeDinas(models.Model):
    _name = 'ka_hr_payroll.employee.dinas'
    _order = 'date_pay desc'
    _inherit = 'mail.thread'

    name = fields.Char(string="Nama Biaya", size=255)
    date_pay = fields.Date(string="Tanggal Dibayar", required=True, default=fields.Date.today, readonly=True,
                           states={'draft': [('readonly', False)]})
    holiday_id = fields.Many2one('hr.holidays', string="Dinas", required=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    nomor_dinas = fields.Char(string="No. SPJ", related='holiday_id.nomor_dinas')
    employee_id = fields.Many2one('hr.employee', related='holiday_id.employee_id', string="Karyawan", store=True)
    duration = fields.Integer(string="Jumlah Hari", required=True, readonly=True,
                              states={'draft': [('readonly', False)]})
    dinas_period_id = fields.Many2one('ka_hr_payroll.dinas.period', string="Periode Dinas", compute='_compute_dinas',
                                      store=True)
    dinas_type = fields.Selection([
        ('1', "Unit/PG"),
        ('2', "Lumpsum")
    ], string="Tipe Dinas", default='1', required=True, readonly=True, states={'draft': [('readonly', False)]})
    # dinas_detail_id = fields.Many2one('ka_hr_payroll.dinas.detail', string="Data Detail Dinas",
    #                                   compute='_compute_dinas_detail', store=True)
    dinas_detail_id = fields.Many2one('ka_hr_payroll.dinas.detail', string="Data Detail Dinas", readonly=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan")
    ], string="Status", default='draft', required=True)
    notes = fields.Text(string="Catatan Persetujuan")
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", readonly=True,
                                         states={'draft': [('readonly', False)]})
    grand_total = fields.Float(string="Grand Total", compute='_compute_grand_total', store=True)
    child_ids = fields.One2many('ka_hr_payroll.employee.dinas.child', 'employee_dinas_id', string="Detail")

    @api.model
    def create(self, vals):
        record = super(KaHrPayrollEmployeeDinas, self).create(vals)
        if 'name' not in vals or not vals.get('name'):
            record.name = "Biaya Dinas {0}".format(record.holiday_id.nomor_dinas)
        return record

    @api.onchange('holiday_id')
    def _onchange_holiday(self):
        self.duration = self.holiday_id.number_of_days_temp

    @api.depends('date_pay', 'employee_id')
    def _compute_dinas(self):
        for ed in self:
            ed.dinas_period_id = None

            if not ed.employee_id:
                ed.company_payroll_id = None
            else:
                ed.company_payroll_id = ed.employee_id.company_payroll_id

            if not ed.date_pay:
                continue

            ed.dinas_period_id = self.env['ka_hr_payroll.dinas.period'].search([
                ('date_start', '<=', ed.date_pay),
                ('status_id', 'parent_of', ed.employee_id.status_id.id),
                ('state', '=', 'done'),
                ('company_payroll_id', '=', ed.company_payroll_id.id)
            ], limit=1, order='date_start desc')

    @api.onchange('dinas_period_id', 'dinas_type')
    def _onchange_dinas_detail(self):
        for ed in self:
            if not ed.dinas_period_id or not ed.dinas_type:
                continue

            params = [
                ('period_id', '=', ed.dinas_period_id.id),
                ('dinas_type', '=', ed.dinas_type),
            ]

            if not ed.dinas_period_id.is_all_status_id:
                dinas_detail = self.env['ka_hr_payroll.dinas.detail'].search(params)
                detail = dinas_detail.filtered(lambda r: ed.employee_id.jabatan_id.id in r.jabatan_ids.ids)
                if detail:
                    ed.dinas_detail_id = detail
                else:
                    ed.dinas_detail_id = None
            else:
                ed.dinas_detail_id = self.env['ka_hr_payroll.dinas.detail'].search(params, limit=1)

            ed._generate_child_template()

    def _generate_child_template(self):
        detail = self.dinas_detail_id
        if detail:
            self.child_ids = None
            for detail_child in detail.child_ids:
                self.env['ka_hr_payroll.employee.dinas.child'].new({
                    'employee_dinas_id': self.id,
                    'detail_child_id': detail_child.id,
                    'dinas_master_id': detail_child.master_id.id,
                    'is_daily': detail_child.is_daily,
                    'value': detail_child.value,
                    'prosentase': 100.00,
                    'total': detail_child.value * (100.00 / 100),
                })

    @api.depends('duration', 'child_ids')
    def _compute_grand_total(self):
        for ed in self:
            ed.grand_total = 0
            if ed.child_ids:
                ed.grand_total = sum([child.total for child in ed.child_ids])

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'canceled'

    def formatting_currency(self, value):
        return format_local_currency(value)


class KaHrPayrollEmployeeDinasChild(models.Model):
    _name = 'ka_hr_payroll.employee.dinas.child'

    employee_dinas_id = fields.Many2one('ka_hr_payroll.employee.dinas', string="Biaya Dinas Karyawan", required=True,
                                        ondelete='cascade')
    detail_child_id = fields.Many2one('ka_hr_payroll.dinas.detail.child', string="Nama Biaya", required=True)
    dinas_master_id = fields.Many2one('ka_hr_payroll.dinas.master', string="Jenis Biaya")
    is_daily = fields.Boolean(string="Dibayar Harian", default=False)
    value = fields.Float(string="Nilai", required=True, default=0.00)
    prosentase = fields.Float(string="Prosentase", required=True, default=100.00)
    total = fields.Float(string="Total", compute='_compute_total', store=True)

    @api.onchange('detail_child_id')
    def _onchange_detail_child(self):
        self.dinas_master_id = self.detail_child_id.master_id
        self.is_daily = self.detail_child_id.is_daily
        self.value = self.detail_child_id.value

    @api.depends('employee_dinas_id.duration', 'is_daily', 'value', 'prosentase')
    def _compute_total(self):
        for child in self:
            child.total = child.value * (child.prosentase / 100)
            if child.is_daily:
                child.total *= child.employee_dinas_id.duration
