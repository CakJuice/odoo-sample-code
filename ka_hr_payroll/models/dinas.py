# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class KaHrPayrollDinas(models.Model):
    _name = 'ka_hr_payroll.dinas.master'

    code = fields.Char(string="Kode", size=4, required=True)
    name = fields.Char(string="Nama", size=128, required=True)
    account_id = fields.Many2one('account.account', string="Nama Akun", company_dependent=True)

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            code = record.code or ''
            name = record.name or ''
            res.append((record.id, '{0} - {1}'.format(code, name)))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        if not args:
            args = []

        if name:
            record = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
        else:
            record = self.search(args, limit=limit)

        return record.name_get()


class KaHrPayrollDinasPeriod(models.Model):
    _name = 'ka_hr_payroll.dinas.period'
    _description = "Periode Biaya Perjalanan Dinas"
    _order = 'date_start desc'

    name = fields.Char(string="Nama", size=255)
    date_start = fields.Date(string="Tanggal Berlaku", default=fields.Date.today, required=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True, readonly=True,
                                states={'draft': [('readonly', False)]})
    is_all_status_id = fields.Boolean(string="Berlaku Semua Status Karyawan", readonly=True,
                                      states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', "Draft"),
        ('done', "Disetujui"),
        ('canceled', "Dibatalkan")
    ], string="Status", default='draft', required=True)
    no_sk = fields.Char(string="Nomor SK", size=24, readonly=True, states={'draft': [('readonly', False)]})
    date_approve = fields.Date(string="Tanggal SK", default=fields.Date.today, required=True, readonly=True,
                               states={'draft': [('readonly', False)]})
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True, readonly=True,
                                         states={'draft': [('readonly', False)]})
    notes = fields.Text(string="Catatan Persetujuan")

    @api.model
    def create(self, vals):
        record = super(KaHrPayrollDinasPeriod, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            date_start_obj = datetime.strptime(record.date_start, DATE_FORMAT)
            date_start_str = date_start_obj.strftime('%d-%m-%Y')
            record.name = "Dinas {0}. Periode: {1}".format(record.status_id.name, date_start_str)
        return record

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'canceled'

    @api.multi
    def action_view_detail(self):
        action = self.env.ref('ka_hr_payroll.action_dinas_detail')
        result = action.read()[0]
        result['domain'] = [('period_id', '=', self.id)]
        result['context'] = {'default_period_id': self.id}
        return result

    @api.multi
    def action_create_detail(self):
        view_id = self.env.ref('ka_hr_payroll.view_dinas_detail_form').id
        action = self.env.ref('ka_hr_payroll.action_dinas_detail')
        result = action.read()[0]
        result['views'] = [(view_id, 'form')]
        result['view_id'] = view_id
        result['domain'] = [('period_id', '=', self.id)]
        result['context'] = {'default_period_id': self.id}
        return result


class KaHrPayrollDinasDetail(models.Model):
    _name = 'ka_hr_payroll.dinas.detail'

    DINAS_TYPE = [
        ('1', "Unit/PG"),
        ('2', "Lumpsum"),
    ]

    name = fields.Char(string="Nama Detail", size=255)
    period_id = fields.Many2one('ka_hr_payroll.dinas.period', string="Periode", required=True)
    jabatan_ids = fields.Many2many('hr.jabatan', 'jabatan_dinas_detail', 'dinas_detail_id', 'jabatan_id',
                                   string="Jabatan")
    period_state = fields.Selection([
        ('draft', "Draft"),
        ('done', "Disetujui"),
        ('canceled', "Dibatalkan")
    ], string="Status", related='period_id.state')
    dinas_type = fields.Selection(DINAS_TYPE, string="Tipe Dinas", default='1', required=True)
    is_all_status_id = fields.Boolean(string="Berlaku Semua Status Karyawan", related='period_id.is_all_status_id')
    child_ids = fields.One2many('ka_hr_payroll.dinas.detail.child', 'detail_id', string="Detail")

    def get_type_name(self, record_key):
        for key, value in self.DINAS_TYPE:
            if key == record_key:
                return value
        return ''

    @api.model
    def create(self, vals):
        record = super(KaHrPayrollDinasDetail, self).create(vals)
        if not 'name' in vals or not vals.get('name'):
            record.name = "Detail {0} - {1}".format(record.period_id.name, record.get_type_name(record.dinas_type))
        return record


class KaHrPayrollDinasDetailChild(models.Model):
    _name = 'ka_hr_payroll.dinas.detail.child'

    detail_id = fields.Many2one('ka_hr_payroll.dinas.detail', string="Detail", required=True)
    master_id = fields.Many2one('ka_hr_payroll.dinas.master', string="Master Dinas", required=True)
    name = fields.Char(string="Nama", size=255, compute='_compute_name', store=True)
    is_daily = fields.Boolean(string="Dibayar Harian", default=False)
    value = fields.Float(string="Nilai", required=True, default=0.00)

    @api.depends('detail_id', 'master_id')
    def _compute_name(self):
        for child in self:
            child.name = '{0} - {1}'.format(child.master_id.name,
                                            child.detail_id.get_type_name(child.detail_id.dinas_type))
