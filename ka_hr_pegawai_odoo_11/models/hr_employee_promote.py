# -*- coding: utf-8 -*-

from calendar import monthrange
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class KaHrEmployeePromote(models.Model):
    """Data history of employee promote.

    _name = 'hr.employee.promote'
    """

    _name = 'hr.employee.promote'
    _inherit = 'mail.thread'

    PROMOTE_TYPE = [
        ('0', "Migrasi Data"),
        ('1', "Promosi / Pemindahan"),
        ('2', "Kenaikan Berkala Unit/PG"),
        ('3', "Pengangkatan Karyawan Tetap"),
        ('4', "Penerimaan Karyawan Baru"),
        ('5', "Kontrak Baru"),
        ('6', "Pensiun"),
        ('7', "Pengunduran Diri"),
        ('8', "Pemecatan"),
        ('9', "Meninggal Dunia"),
    ]

    name = fields.Char(string="Nama", size=255)
    employee_id = fields.Many2one('hr.employee', string="Karyawan", required=True, ondelete='cascade')
    date_start = fields.Date(string="Tanggal Mulai", required=True, default=fields.Date.today)
    is_contract = fields.Boolean(string="Kontrak", default=False)
    date_end = fields.Date(string="Tanggal Akhir")
    department_id = fields.Many2one('hr.department', string="Department Baru")
    jabatan_id = fields.Many2one('hr.jabatan', string="Jabatan Baru")
    pangkat_id = fields.Many2one('hr.pangkat', string="Pangkat Baru")
    golongan_id = fields.Many2one('hr.golongan', string="Golongan Baru")
    status_id = fields.Many2one('hr.status', string="Status Baru")
    company_id = fields.Many2one('res.company', string="Unit/PG Baru")
    promote_type = fields.Selection(PROMOTE_TYPE, string="Tipe", default='1', required=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('processed', "Diproses"),
        ('done', "Selesai"),
        ('canceled', "Dibatalkan"),
    ], string="Status", required=True, default='draft', track_visibility='onchange')
    date_approve = fields.Datetime(string="Tanggal Disetujui")
    date_done = fields.Datetime(string="Tanggal Selesai")
    no_sk = fields.Char(string="Nomor SK", size=24)
    notes = fields.Text(string="Catatan Persetujuan")

    old_promote_id = fields.Many2one('hr.employee.promote', compute='_compute_old_promote',
                                     string="Ref. Data Lama", store=True)
    old_department_id = fields.Many2one('hr.department', compute='_compute_old_promote',
                                        string="Department Lama", store=True)
    old_jabatan_id = fields.Many2one('hr.jabatan', compute='_compute_old_promote',
                                     string="Jabatan Lama", store=True)
    old_pangkat_id = fields.Many2one('hr.pangkat', compute='_compute_old_promote',
                                     string="Pangkat Terakhir", store=True)
    old_golongan_id = fields.Many2one('hr.golongan', compute='_compute_old_promote',
                                      string="Golongan Terakhir", store=True)
    old_status_id = fields.Many2one('hr.status', compute='_compute_old_promote',
                                    string="Status Terakhir", store=True)
    old_company_id = fields.Many2one('res.company', compute='_compute_old_promote',
                                     string="Unit/PG Terakhir", store=True)

    new_promote_ids = fields.One2many('hr.employee.promote', 'old_promote_id', string="Ref. History Promosi Baru")

    # @api.constrains('employee_id', 'promote_type')
    # def _check_valid(self):
    #     for promote in self:
    #         if promote.employee_id.pensiun:
    #             raise ValidationError("Karyawan sudah berhenti, tidak bisa membuat promosi/history baru.")

    def _get_type_name(self, key):
        """To get type name of `scale_type` value.

        Arguments:
            key {String} -- `scale_type` value.

        Returns:
            String -- Result of `scale_type` value check.
        """
        for _type in self.PROMOTE_TYPE:
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
        promote_count = self.search_count([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'draft')
        ])
        if promote_count > 0:
            raise ValidationError(
                "Ada data history promosi yang belum diproses!. Anda tidak dapat melanjutkan aksi ini.")

        record = super().create(vals)
        if 'name' not in vals or not vals.get('name'):
            date_start_obj = datetime.strptime(record.date_start, DATE_FORMAT)
            date_start_str = date_start_obj.strftime('%d-%m-%Y')
            record.name = "{0} - {1}. Periode: {2}".format(record.employee_id.name,
                                                           self._get_type_name(record.promote_type), date_start_str)
        return record

    @api.onchange('department_id')
    def _onchange_department(self):
        self.company_id = None
        if self.department_id:
            self.company_id = self.department_id.company_id

    @api.onchange('promote_type', 'employee_id')
    def _onchange_promote(self):
        if self.promote_type == '5':
            self.is_contract = True
        elif self.promote_type == '6':
            self.date_start = self.employee_id.tgl_pensiun
        else:
            self.date_start = fields.Date.today()
            self.is_contract = False

    def get_last_processed_promote(self, employee_id, date_start=None):
        """To get data processed promote of employee.

        Arguments:
            employee_id {Int} -- ID of `hr.employee`.

        Returns:
            Recordset -- Result of query with limit `1` and order by `date_start desc`.
        """
        if not date_start:
            date_start = fields.Date.today()
        return self.search([
            ('date_start', '<=', date_start),
            ('employee_id', '=', employee_id),
            ('promote_type', 'not in', ['6', '7', '8', '9']),
            ('state', 'in', ['processed', 'done']),
        ], limit=1, order='date_start desc')

    def get_employee_actual_promote(self, employee_id, month, year):
        """Get actual data promote by employee.

        Arguments:
            employee_id {Int} -- ID of `hr.employee`.
            month {Int} -- Month which want to search promote.
            year {Int} -- Year which want to search promote.

        Returns:
            Recordset -- Result of query with limit `1` and order by `date_start desc`.
        """
        last_day = monthrange(year, month)[1]
        month_str = '0{0}'.format(month) if month < 10 else str(month)
        date_obj = datetime.strptime('{0}-{1}-{2}'.format(year, month_str, last_day), DATE_FORMAT)
        date_str = date_obj.strftime(DATE_FORMAT)
        return self.get_last_processed_promote(employee_id, date_start=date_str)

    def get_draft_promote(self, employee_id):
        """Get only promote with `state='draft'`.

        Arguments:
            employee_id {Int} -- ID of `hr.employee`.

        Returns:
            Recordset -- Result of query with limit `1` and order by `date_start desc`.
        """
        return self.search([
            ('date_start', '<=', fields.Date.today()),
            ('employee_id', '=', employee_id),
            ('promote_type', 'not in', ['6', '7', '8', '9']),
            ('state', '=', 'draft'),
        ], order='date_start desc')

    def get_last_promote(self, employee_id):
        """To get data promote of employee.

        Arguments:
            employee_id {Int} -- ID of `hr.employee`.

        Returns:
            Recordset -- Result of query with limit `1` and order by `date_start desc`.
        """
        return self.search([
            ('date_start', '<=', fields.Date.today()),
            ('employee_id', '=', employee_id),
            ('promote_type', 'not in', ['6', '7', '8', '9']),
            ('state', '=', 'done'),
        ], limit=1, order='date_start desc')

    @api.depends('employee_id')
    def _compute_old_promote(self):
        """Computing old last promote.
        """
        for promote in self:
            if promote.old_promote_id:
                # data sudah ada

                continue

            last_promote = promote.get_last_processed_promote(promote.employee_id.id)
            if last_promote:
                if last_promote.id == promote.id:
                    continue
                # set data old_ dr data promote terakhir yg berstatus minimal 'processed'
                self._assign_new_value(promote, last_promote)

    def action_draft(self):
        """Set `state = 'draft'`.
        """
        self.state = 'draft'

    def action_process(self):
        """Set `state = 'processed'`.
        """
        # date_start_obj = datetime.strptime(self.date_start, DATE_FORMAT)
        # date_now_obj = datetime.strptime(fields.Date.today(), DATE_FORMAT)
        # if date_start_obj > date_now_obj:
        #     raise ValidationError("Tidak bisa diproses, tanggal mulai > tanggal sekarang.")

        self.state = 'processed'
        # setelah diapprove maka data di hr.employee diupdate.
        self._assign_employee_new_value()

        # untuk data promosi lain yg masih draft (jika ada), diupdate data old_ menjadi data sekarang
        draft_promote = self.get_draft_promote(self.employee_id.id)
        for draft in draft_promote:
            self._assign_new_value(draft, self)

        if self.promote_type == '4':
            self.employee_id.tgl_masuk = self.date_start
            self.employee_id.tgl_cuti = self.date_start
        elif self.promote_type == '5':
            self.employee_id.pensiun = False
            self.employee_id.stop_type = None
            self.employee_id.is_contract = self.is_contract
            self.employee_id.date_contract_start = self.date_start
            self.employee_id.date_contract_end = self.date_end
            self.employee_id.tgl_cuti = self.date_start
        elif self.promote_type in ['6', '7', '8', '9']:
            self.employee_id.pensiun = True
            self.employee_id.stop_type = self.promote_type

    def action_approve(self):
        """Set `state = 'approve'` and set `date_approve` if not set yet.
        """
        if not self.date_approve:
            self.date_approve = fields.Datetime.now()
        self.action_done()

    def action_done(self):
        """Set `state = 'done'` and set `date_done` if not set yet.
        """
        if not self.date_done:
            self.date_done = fields.Datetime.now()
        self.state = 'done'
        if self.promote_type == '3':
            # pengangkatan karyawan tetap
            self.employee_id.is_tetap = True
            self.employee_id.tgl_tetap = self.date_start

    def _clean_old_value(self, obj):
        obj.old_promote_id = None
        obj.old_department_id = None
        obj.old_jabatan_id = None
        obj.old_pangkat_id = None
        obj.old_golongan_id = None
        obj.old_status_id = None
        obj.old_company_id = None

    def _assign_new_value(self, obj, assign_obj):
        obj.old_promote_id = assign_obj
        obj.old_department_id = assign_obj.department_id
        obj.old_jabatan_id = assign_obj.jabatan_id
        obj.old_pangkat_id = assign_obj.pangkat_id
        obj.old_golongan_id = assign_obj.golongan_id
        obj.old_status_id = assign_obj.status_id
        obj.old_company_id = assign_obj.company_id

    def _assign_old_value(self, obj, assign_obj):
        obj.old_promote_id = assign_obj.old_promote_id
        obj.old_department_id = assign_obj.old_department_id
        obj.old_jabatan_id = assign_obj.old_jabatan_id
        obj.old_pangkat_id = assign_obj.old_pangkat_id
        obj.old_golongan_id = assign_obj.old_golongan_id
        obj.old_status_id = assign_obj.old_status_id
        obj.old_company_id = assign_obj.old_company_id

    def _assign_employee_old_value(self):
        self.employee_id.department_id = self.old_department_id
        self.employee_id.jabatan_id = self.old_jabatan_id
        self.employee_id.pangkat_id = self.old_pangkat_id
        self.employee_id.golongan_id = self.old_golongan_id
        self.employee_id.status_id = self.old_status_id
        self.employee_id.company_id = self.old_company_id

    def _assign_employee_new_value(self):
        self.employee_id.department_id = self.department_id
        self.employee_id.jabatan_id = self.jabatan_id
        self.employee_id.pangkat_id = self.pangkat_id
        self.employee_id.golongan_id = self.golongan_id
        self.employee_id.status_id = self.status_id
        self.employee_id.company_id = self.company_id

    def get_last_stop_history(self, employee_id):
        return self.search([
            ('employee_id', '=', employee_id),
            ('promote_type', 'in', ['6', '7', '8', '9'])
        ], limit=1, order='date_start desc')

    def action_cancel(self):
        """Set `state = 'cancel'` and set `date_done` if not set yet.
        """
        if self.state != 'draft':
            if self.employee_id.last_processed_promote == self:
                self._assign_employee_old_value()
            # check all promote which has `old_promote_id` related with this record.
            # assign all `old_promote` in `new_promote_ids`` which related with this record,
            # with value of this 'old' record
            for new in self.new_promote_ids:
                if self.old_promote_id:
                    self._assign_old_value(new, self)
                else:
                    self._clean_old_value(new)
            self._clean_old_value(self)
            if self.promote_type == '4':
                self.employee_id.tgl_masuk = None
                self.employee_id.tgl_cuti = None
            elif self.promote_type == '5':
                # Jika kontrak dibatalkan, cek apakah sebelumnya sudah pernah pensiun/berhenti
                # Jika sudah pernah pensiun/berhenti maka status pensiun karyawan dikembalikan
                last_stop = self.get_last_stop_history(self.employee_id.id)
                if last_stop:
                    self.employee_id.pensiun = True
                    self.employee_id.stop_type = last_stop.promote_type
                self.employee_id.is_contract = False
                self.employee_id.date_contract_start = None
                self.employee_id.date_contract_end = None
                self.employee_id.tgl_cuti = None
            elif self.promote_type in ['6', '7', '8', '9']:
                self.employee_id.pensiun = False
                self.employee_id.stop_type = None

        self.state = 'canceled'

    @api.multi
    def unlink(self):
        for promote in self:
            promote.action_cancel()
        return super().unlink()
