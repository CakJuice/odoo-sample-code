# -*- coding: utf-8 -*-

import base64
import calendar
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class KaHrEmployeeSP(models.Model):
    """Data of employee's surat peringatan

    _name = 'hr.employee.sp'
    """

    _name = 'hr.employee.sp'
    _description = "SDM Surat Peringatan"
    _order = 'id desc'
    _inherit = 'mail.thread'
    # _REPORT_NAME = 'ka_hr_pegawai.report_ka_hr_employee_sp_view'

    NAME_TELAT_WEEKLY = "Surat Peringatan I (Pertama)"
    ACUAN_TELAT_WEEKLY = """Bab II Pasal 5 Ayat 9a, yang berbunyi: \"Datang terlambat 2 kali dalam seminggu, tanpa alasan yang bisa diterima.\""""
    ALASAN_TELAT_WEEKLY = "Datang terlambat pada "
    NAME_TELAT_MONTHLY = "Surat Peringatan I (Pertama)"
    ACUAN_TELAT_MONTHLY = """Bab II Pasal 5 Ayat 9a, yang berbunyi: \"Datang terlambat 3 kali dalam sebulan, tanpa alasan yang bisa diterima.\""""
    ALASAN_TELAT_MONTHLY = "Datang terlambat pada "

    nomor = fields.Char(string="No. SP", size=64, required=True, default='/')
    date_sp = fields.Date(string="Tanggal SP", required=True, default=fields.Date.today)
    name = fields.Char(string="Deskripsi SP", required=True)
    employee_id = fields.Many2one('hr.employee', string="Nama Pegawai", required=True, domain=[('pensiun', '=', False)])
    level = fields.Selection([
        (1, 'SP 1'),
        (2, 'SP 2'),
        (3, 'SP 3'),
    ], default=1, required=True)
    acuan = fields.Text(string="Acuan", required=True)
    alasan = fields.Text(string="Alasan", required=True)
    company_id = fields.Many2one('res.company', compute='_compute_employee', string="Unit/PG")
    state = fields.Selection([
        ('draft', "Draft"),
        ('approved', "Disetujui"),
        ('canceled', "Dibatalkan"),
    ], string="Status", default='draft', track_visibility='onchange')

    # _sql_constraints = [
    # 	('hr_employee_sp_unique', 'UNIQUE(nomor, company_id)', "Nomor SP sudah ada! Tidak boleh sama!")
    # ]

    def create_sp_telat_weekly(self, employee_id, str_date):
        return self.create({
            'employee_id': employee_id,
            'name': self.NAME_TELAT_WEEKLY,
            'acuan': self.ACUAN_TELAT_WEEKLY,
            'alasan': self.ALASAN_TELAT_WEEKLY + " {}.".format(str_date, ),
        })

    def create_sp_telat_monthly(self, employee_id, str_date):
        return self.create({
            'employee_id': employee_id,
            'name': self.NAME_TELAT_MONTHLY,
            'acuan': self.ACUAN_TELAT_MONTHLY,
            'alasan': self.ALASAN_TELAT_MONTHLY + " {}.".format(str_date, ),
        })

    @api.depends('employee_id')
    def _compute_employee(self):
        for sp in self:
            sp.company_id = sp.employee_id.company_id

    @api.model
    def create(self, vals):
        # get company_id by employee"""
        if 'company_id' not in vals:
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals['company_id'] = employee.company_id.id

        """Customize sequence date_range"""
        sequence = self.env['ir.sequence'].search([
            ('code', 'like', self._name + '%'),
            ('company_id', '=', vals['company_id'])
        ], limit=1)

        if sequence:
            date_now = datetime.now().date()
            is_create_range = False
            if sequence.date_range_ids and len(sequence.date_range_ids) > 0:
                last_range = sequence.date_range_ids[-1]
                date_to_obj = datetime.strptime(last_range.date_to, DATE_FORMAT)
                if date_to_obj.month != date_now.month:
                    is_create_range = True
            else:
                is_create_range = True

            if is_create_range:
                last_day = calendar.monthrange(date_now.year, date_now.month)[1]
                date_range = self.env['ir.sequence.date_range'].create({
                    'number_next': 1,
                    'date_from': '{}-{}-01'.format(date_now.year, date_now.month),
                    'date_to': '{}-{}-{}'.format(date_now.year, date_now.month, last_day),
                    'sequence_id': sequence.id
                })
                date_range._cr.commit()

            vals['nomor'] = sequence.next_by_id()
            return super().create(vals)
        else:
            raise ValidationError("Nomor urutan belum diset! Hubungi Administrator!")

    def get_ttd_dirut(self):
        return self.company_id.dept_dirut.manager_id.name

    def get_ttd_jabatan(self):
        return self.company_id.dept_dirut.manager_id.jabatan_id.name

    def get_email_cc(self):
        return self.company_id.dept_sdm.manager_id.work_email or ''

    def get_subject_name(self):
        return '{}_({})'.format(self.name, self.nomor).replace(' ', '_')

    def _get_attachment(self):
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)
        ], limit=1)

        attachment_name = self.get_subject_name()

        pdf = self.env.ref('ka_hr_pegawai.report_ka_hr_employee_sp').render_qweb_pdf([self.id])
        b64_pdf = base64.b64encode(pdf[0])
        if attachment:
            attachment.write({
                'name': attachment_name,
                'type': 'binary',
                'datas': b64_pdf,
                'datas_fname': attachment_name + ".pdf",
                'store_fname': attachment_name,
                'mimetype': 'application/x-pdf',
            })

            self._cr.commit()
        else:
            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': b64_pdf,
                'datas_fname': attachment_name + ".pdf",
                'store_fname': attachment_name,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/x-pdf',
            })
            self._cr.commit()

        return attachment

    def _remove_attachment(self):
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)
        ], limit=1)

        if attachment:
            attachment.unlink()
            self._cr.commit()

    @api.multi
    def action_draft(self):
        for sp in self:
            sp.state = 'draft'
            sp._remove_attachment()

    @api.multi
    def action_approve(self):
        for sp in self:
            if not sp.employee_id.work_email or not sp.company_id.email:
                raise ValidationError("Email pegawai belum diisi!")
            if not sp.company_id.email:
                raise ValidationError("Email Unit/PG belum diisi!")

            sp.state = 'approved'
            attachment = sp._get_attachment()
            template = sp.env.ref('ka_hr_pegawai.template_mail_employee_sp_approved')
            mail = sp.env['mail.template'].browse(template.id)
            mail.attachments_ids = attachment
            sp._cr.commit()
            mail.send_mail(sp.id)
            mail.attachments_ids = None
            sp._cr.commit()
            sp.env.user.notify_info("Email pemberitahuan persetujuan sudah dikirim ke karyawan yang bersangkutan!")

    @api.multi
    def action_cancel(self):
        for sp in self:
            old_state = sp.state
            sp.state = 'canceled'
            sp._remove_attachment()

            if old_state == 'draft':
                continue

            template = sp.env.ref('ka_hr_pegawai.template_mail_employee_sp_canceled')
            mail = sp.env['mail.template'].browse(template.id)
            mail.send_mail(sp.id)
            sp.env.user.notify_info("Email pemberitahuan pembatalan sudah dikirim ke karyawan yang bersangkutan!")
