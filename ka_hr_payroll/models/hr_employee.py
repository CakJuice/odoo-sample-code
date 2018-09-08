# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from calendar import monthrange
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class KaHrPayrollEmployee(models.Model):
    """Master data of employee.

    _inherit = 'hr.employee'
    """

    _inherit = 'hr.employee'

    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True)
    payroll_department_id = fields.Many2one('hr.department', compute='_compute_info', string="Divisi Penggajian")
    payroll_jabatan_id = fields.Many2one('hr.jabatan', compute='_compute_info', string="Jabatan Penggajian")
    payroll_pangkat_id = fields.Many2one('hr.pangkat', compute='_compute_info', string="Pangkat Penggajian")
    payroll_golongan_id = fields.Many2one('hr.golongan', compute='_compute_info', string="Golongan Penggajian")
    payroll_status_id = fields.Many2one('hr.status', compute='_compute_info', string="Status Penggajian")
    payroll_company_id = fields.Many2one('res.company', compute='_compute_info', string="Unit/PG Penggajian")
    scale = fields.Float(string="Skala", digits=(6, 3), compute='_compute_info')

    payroll_golongan_khusus_id = fields.Many2one('hr.golongan', string="Golongan Khusus",
                                                 help="Digunakan untuk tunjangan khusus. Jika tidak diisi maka nilai golongan sama dengan 'Golongan Penggajian'")
    # japres = fields.Float(string="Jasa Prestasi", digits=(5, 2), compute='_compute_info')

    gaji_pokok = fields.Float(string="Gaji Pokok", compute='_compute_salary')
    tunjangan_rumah = fields.Float(string="Tunj. Rumah", compute='_compute_salary')
    tunjangan_jabatan = fields.Float(string="Tunj. Jabatan", compute='_compute_salary')
    tunjangan_khusus = fields.Float(string="Tunj. Khusus", compute='_compute_tunjangan_khusus')
    tunjangan_representasi = fields.Float(string="Tunj. Representasi", compute='_compute_tunjangan_representasi')

    potongan_ids = fields.One2many('ka_hr_payroll.potongan.employee', 'employee_id', string="Data Potongan")

    @api.multi
    def _compute_info(self):
        """Override
        Computing info of employee based from `hr.employee.promote`.
        """
        for employee in self:
            if employee.pensiun:
                continue

            last_promote = self.env['hr.employee.promote'].get_last_promote(employee.id)
            if last_promote:
                employee.payroll_department_id = last_promote.department_id
                employee.payroll_jabatan_id = last_promote.jabatan_id
                employee.payroll_pangkat_id = last_promote.pangkat_id
                employee.payroll_golongan_id = last_promote.golongan_id
                employee.payroll_status_id = last_promote.status_id
                employee.payroll_company_id = last_promote.company_id
                employee.scale = last_promote.scale
                # employee.japres = last_promote.japres

    @api.multi
    def _compute_tunjangan_representasi(self):
        """To compute `tunjangan_representasi` based on `ka_hr_payroll.tunjangan.representasi`.

        Decorators:
            api.depends('jabatan_id', 'company_payroll_id')
        """
        for employee in self:
            employee.tunjangan_representasi = 0.0
            if employee.pensiun:
                continue

            if not employee.company_id.is_tunjangan_representasi:
                continue

            tunjangan = self.env['ka_hr_payroll.tunjangan.representasi'].get_last_tunjangan(
                employee.payroll_status_id.id, employee.company_payroll_id.id)

            if tunjangan:
                tunjangan_lines = self.env['ka_hr_payroll.tunjangan.representasi.lines'].search([
                    ('tunjangan_id', '=', tunjangan.id),
                    ('jabatan_id', '=', employee.payroll_jabatan_id.id)
                ], limit=1)

                if tunjangan_lines:
                    employee.tunjangan_representasi = tunjangan_lines.value

    @api.multi
    def _compute_tunjangan_khusus(self):
        """To compute `tunjangan_khusus` based on `ka_hr_payroll.tunjangan.khusus`.

        Decorators:
            api.depends('pangkat_id', 'jabatan_id', 'golongan_id')
        """
        for employee in self:
            employee.tunjangan_khusus = 0.0
            if employee.pensiun:
                continue

            if not employee.company_id.is_tunjangan_khusus:
                continue

            _golongan_id = employee.payroll_golongan_khusus_id.id if employee.payroll_golongan_khusus_id \
                else employee.payroll_golongan_id.id

            combine = self.env['ka_hr_payroll.tunjangan.khusus.combine'].get_combine(employee.payroll_jabatan_id.id,
                                                                                     _golongan_id,
                                                                                     employee.payroll_pangkat_id.id,
                                                                                     employee.company_payroll_id.id)

            if combine:
                tunj_period = self.env['ka_hr_payroll.tunjangan.khusus.period'].get_last_period(
                    employee.payroll_status_id.id, employee.company_payroll_id.id)

                if tunj_period:
                    tunj_period_lines = self.env['ka_hr_payroll.tunjangan.khusus.period.lines'].search([
                        ('period_id', '=', tunj_period.id),
                        ('combine_id', '=', combine.id),
                    ], limit=1)

                    if tunj_period_lines:
                        employee.tunjangan_khusus = tunj_period_lines.value

    @api.multi
    def _compute_salary(self):
        """To compute salary (gapok, tj.rumah, tj.jabatan).
        Depends of scale, golongan_id and status_id of employee.

        Decorators:
            api.depends('scale', 'golongan_id', 'status_id', 'company_payroll_id')
        """
        payroll_config = self.env['ka_hr_payroll.config'].default_config()
        for employee in self:
            if employee.pensiun:
                continue

            if employee.payroll_status_id.is_default_payroll:
                # Gaji sudah ditetapkan
                company_default = self.env['ka_hr_payroll.company.default'].get_last_default(
                    employee.payroll_status_id.id,
                    employee.company_payroll_id.id, config=payroll_config)
                employee.gaji_pokok = company_default.gaji_pokok or 0.0
                employee.tunjangan_rumah = company_default.tunjangan_rumah or 0.0
                employee.tunjangan_jabatan = company_default.tunjangan_jabatan or 0.0
                employee.tunjangan_khusus = company_default.tunjangan_khusus or 0.0
                employee.tunjangan_representasi = company_default.tunjangan_representasi or 0.0
            else:
                employee.gaji_pokok = employee.generate_salary_scale(employee, 'gp')

                if employee.company_id.is_tunjangan_jabatan:
                    employee.tunjangan_jabatan = self.generate_salary_scale(employee, 'tj')
                else:
                    employee.tunjangan_jabatan = 0.0

                if employee.company_id.is_tunjangan_rumah:
                    employee.tunjangan_rumah = self.generate_salary_scale(employee, 'tr')
                else:
                    employee.tunjangan_rumah = 0.0

    def generate_salary_scale(self, employee, scale_type):
        """To generate salary based of employee scale.

        Arguments:
            employee {Recordset} -- Employee which want to get salary.
            scale_type {String} -- Type of employee salary ('gp', 'tr', 'tj').
                See `ka_hr_payroll.scale` in `type` field.
        """
        salary = 0.0
        if employee.scale and employee.payroll_golongan_id and scale_type in ['gp', 'tr', 'tj']:
            scale_period = self.env['ka_hr_payroll.scale.period'].get_last_period(employee.payroll_status_id.id,
                                                                                  scale_type,
                                                                                  employee.company_payroll_id.id)

            if scale_period:
                scale = self.env['ka_hr_payroll.scale'].get_last_scale(scale_period.id,
                                                                       employee.payroll_golongan_id.id)

                if scale:
                    scale_lines = self.env['ka_hr_payroll.scale.lines'].get_last_lines(scale.id, employee.scale)

                    if scale_lines:
                        salary = scale_lines.value
        return salary

    def get_gaji_konjungtur(self, last_konjungtur_gaji=None, payroll_date=None):
        """To get gaji_pokok * konjungtur, depends on config.

        Keyword Arguments:
            last_konjungtur_gaji {Recordset} -- Record of last konjungtur from `ka_hr_payroll.company.konjungtur
                (default: {None})

        Returns:
            Dict -- Result of gaji_pokok * konjungtur and is_multiply_konjungtur.
        """
        if not last_konjungtur_gaji:
            config = self.env['ka_hr_payroll.config'].default_config()
            last_konjungtur_gaji = self.env['ka_hr_payroll.company.konjungtur'].get_last_konjungtur('1',
                                                                                                    self.company_payroll_id.id,
                                                                                                    config=config,
                                                                                                    payroll_date=payroll_date)

        gapok_total = self.gaji_pokok
        is_multiply_konjungtur = self.payroll_status_id.is_multiply_konjungtur
        if is_multiply_konjungtur:
            gapok_total *= last_konjungtur_gaji.value / 100.0

        return {'gapok_total': gapok_total, 'is_multiply_konjungtur': is_multiply_konjungtur}

    def _get_masuk_month_diff(self, date_check):
        """To check date diff between `tgl_masuk` and `date_check`.

        Arguments:
            date_check {String} -- String of date.

        Returns:
            int -- Result of month diff.
        """
        tgl_masuk_obj = datetime.strptime(self.tgl_masuk, DATE_FORMAT)
        date_check_obj = datetime.strptime(date_check, DATE_FORMAT)
        selisih = relativedelta(date_check_obj, tgl_masuk_obj)
        return selisih.years * 12 + selisih.months

    def _get_data_tunjangan(self, payroll_type):
        data = {
            'is_tunjangan_rumah': False,
            'tunjangan_rumah': 0,
            'is_tunjangan_jabatan': False,
            'tunjangan_jabatan': 0,
            'is_tunjangan_khusus': False,
            'tunjangan_khusus': 0,
            'is_tunjangan_representasi': False,
            'tunjangan_representasi': 0,
            'multiply_value': 1.00,
        }
        if payroll_type == '1':
            # gaji bulanan
            data['is_tunjangan_rumah'] = self.payroll_company_id.is_tunjangan_rumah
            data['is_tunjangan_jabatan'] = self.payroll_company_id.is_tunjangan_jabatan
            data['is_tunjangan_khusus'] = self.payroll_company_id.is_tunjangan_khusus
            data['is_tunjangan_representasi'] = self.payroll_company_id.is_tunjangan_representasi
        else:
            # THR
            data['is_tunjangan_rumah'] = self.payroll_company_id.thr_tunjangan_rumah
            data['is_tunjangan_jabatan'] = self.payroll_company_id.thr_tunjangan_jabatan
            data['is_tunjangan_khusus'] = self.payroll_company_id.thr_tunjangan_khusus
            data['is_tunjangan_representasi'] = self.payroll_company_id.thr_tunjangan_representasi
            data['multiply_value'] = self.status_id.thr_multiply

        if data['is_tunjangan_rumah']:
            data['tunjangan_rumah'] = self.tunjangan_rumah
        if data['is_tunjangan_jabatan']:
            data['tunjangan_jabatan'] = self.tunjangan_jabatan
        if data['is_tunjangan_khusus']:
            data['tunjangan_khusus'] = self.tunjangan_khusus
        if data['is_tunjangan_representasi']:
            data['tunjangan_representasi'] = self.tunjangan_representasi

        return data

    def generate_payroll(self, data_payroll, config=None):
        """Generate payroll on this employee.

        Arguments:
            data_payroll {Dict} -- Payroll data that is being processed. Related with `ka_hr_payroll.payroll'.
            config {Recordset} -- Default configuration of payroll. Related with `ka_hr_payroll.config`.
        """
        if not self.tgl_masuk:
            return

        if not config:
            config = self.env['ka_hr_payroll.config'].default_config()

        payroll = data_payroll.get('payroll')

        selisih_month = 0
        if payroll.payroll_type == '2':
            # jika THR maka dicek apakah employee sudah layak mendapat THR
            selisih_month = self._get_masuk_month_diff(payroll.date_payroll)
            if selisih_month < config.min_month_thr_proportion:
                return

        last_konjungtur_gaji = data_payroll.get('last_konjungtur_gaji')
        last_konjungtur_dapen = data_payroll.get('last_konjungtur_dapen')

        # gaji_konjungtur = self.get_gaji_konjungtur(last_konjungtur_gaji=last_konjungtur_gaji)
        # gapok_total = gaji_konjungtur.get('gapok_total')
        # is_multiply_konjungtur = gaji_konjungtur.get('is_multiply_konjungtur')
        is_multiply_konjungtur = self.payroll_status_id.is_multiply_konjungtur

        if self.gaji_pokok <= 0:
            return

        data_payroll_employee = {
            'payroll_id': payroll.id,
            'employee_id': self.id,
            # 'payroll_year_period': payroll.year_period,
            # 'payroll_month_period': payroll.month_period,
            'employee_company_id': self.payroll_company_id.id,
            'employee_status_id': self.payroll_status_id.id,
            'is_multiply_konjungtur': is_multiply_konjungtur,
            'is_proportion': False,
            'gaji_pokok': self.gaji_pokok,
            # 'gapok_total': gapok_total,
            'konjungtur_gaji': last_konjungtur_gaji.value,
            'konjungtur_dapen': last_konjungtur_dapen.value,
            'rapel': 0,
        }

        # Penghitungan payroll tergantung kondisi di setting Unit/PG
        data_payroll_employee.update(self._get_data_tunjangan(payroll.payroll_type))

        # cek proporsi
        if payroll.payroll_type == '1':
            # proporsi gaji bulanan untuk HKB yg masa kerja < 1 bulan
            # if config.is_gaji_proportion:
            if self.payroll_status_id.is_gaji_proportion:
                tgl_masuk_obj = datetime.strptime(self.tgl_masuk, DATE_FORMAT)
                _last = monthrange(int(payroll.year_period), payroll.month_period)[1]
                last_date = datetime.strptime('{0}-{1}-{2}'.format(payroll.year_period, payroll.month_period, _last),
                                              DATE_FORMAT)
                selisih = (last_date - tgl_masuk_obj).days + 1
                if selisih < _last and selisih > 0:
                    data_payroll_employee['is_proportion'] = True
                    data_payroll_employee['proportion_value'] = '{0}/{1}'.format(selisih, _last)
        else:
            # jika selisih > config.min_month_thr_full (12) maka mendapat THR penuh tanpa proporsional
            if selisih_month < config.min_month_thr_full:
                data_payroll_employee['is_proportion'] = True
                data_payroll_employee['proportion_value'] = '{0}/{1}'.format(selisih_month,
                                                                             config.month_thr_proportion_value)

        payroll_employee = self.env['ka_hr_payroll.payroll.employee'].create(data_payroll_employee)

        # Hanya gaji bulanan yg menghitung rapel dan potongan.
        if payroll.payroll_type != '1':
            return

        self._generate_rapel(payroll, payroll_employee, data_payroll.get('company_rapel'))
        if not payroll_employee.is_proportion:
            # Jika gaji bulanan ada proporsi, maka tidak kena potongan
            self._generate_potongan(last_konjungtur_dapen, payroll_employee)

    def _generate_rapel(self, payroll, payroll_employee, company_rapel):
        rapel_start = []
        rapel_end = []
        if company_rapel:
            for cr in company_rapel:
                # company_rapel harus divalidasi. apakah employee status_id anggota dari company_rapel.status_id
                rapel = cr.get('rapel')
                if hasattr(rapel, 'status_id'):
                    # rapel yg punya status_id = rapel_company_default, rapel_scale, ->
                    # rapel_tunjangan_khusus, rapel_tunjangan_representasi
                    if rapel.status_id != self.status_id:
                        continue
                else:
                    # rapel company_konjungtur, jika employee status tidak dikali konjungtur ->
                    # maka rapel diabaikan
                    if not self.status_id.is_multiply_konjungtur:
                        continue

                rapel_start.append(datetime.strptime(cr.get('date_start'), DATETIME_FORMAT))
                rapel_end.append(datetime.strptime(cr.get('date_end'), DATETIME_FORMAT))

        # cari rapel dari history promote milik employee yg akan dibayar bulan ini
        rapel_promote = self.env['ka_hr_payroll.rapel.hr.employee.promote'].get_employee_rapel_pay(
            payroll.year_period, payroll.month_period, self.id)

        if rapel_promote:
            for rapel in rapel_promote:
                # rapel_month_list += rapel.get_list_rapel_month()
                rapel_start.append(datetime.strptime(rapel.date_start, DATETIME_FORMAT))
                rapel_end.append(datetime.strptime(rapel.date_end, DATETIME_FORMAT))
                rapel.action_done(payroll)

        # if rapel_month_list:
        if rapel_start and rapel_end:
            # sort rapel_start & rapel_end
            # get smallest value of rapel_start * highest value of rapel_end
            rapel_start.sort()
            rapel_end.sort()
            date_start = rapel_start[0].strftime(DATETIME_FORMAT)
            date_end = rapel_end[-1].strftime(DATETIME_FORMAT)

            # cari data payroll lama sesuai dengan bulan & tahun rapel.
            old_payroll_employee = self.env['ka_hr_payroll.payroll.employee'].search([
                ('employee_id', '=', self.id),
                ('payroll_date', '>=', date_start),
                ('payroll_date', '<=', date_end),
            ])

            # jika data payroll lama ditemukan, maka rapel bisa dibayarkan.
            # jika tidak ditemukan maka employee tidak mendapat rapel.
            for old in old_payroll_employee:
                temp_rapel = old.total_pre_rapel
                if old.payroll_type == '1':
                    temp_penerimaan = payroll_employee.total_pre_rapel
                else:
                    # jika THR cek multiply_value
                    # cek old payroll, penghitungan selisih bukan dari payroll_employee.total_pre_rapel
                    # misal di payroll lama tidak ada tunjangan_rumah, jd penghitungannya payroll_employee jg tanpa tunj_rumah.
                    temp_penerimaan = payroll_employee.gapok_total
                    if old.is_tunjangan_rumah:
                        temp_penerimaan += payroll_employee.tunjangan_rumah
                    if old.is_tunjangan_jabatan:
                        temp_penerimaan += payroll_employee.tunjangan_jabatan
                    if old.is_tunjangan_khusus:
                        temp_penerimaan += payroll_employee.tunjangan_khusus
                    if old.is_tunjangan_representasi:
                        temp_penerimaan += payroll_employee.tunjangan_representasi
                    temp_penerimaan *= old.multiply_value
                    temp_rapel *= old.multiply_value

                # cek tambahan total_penerimaan, karena bisa jadi sudah ada rapel pada bulan itu
                payroll_rapel = self.env['ka_hr_payroll.payroll.employee.rapel'].search([
                    ('payroll_rapel_ref_id', '=', old.id),
                ])

                for pr in payroll_rapel:
                    temp_rapel += pr.payroll_rapel_value

                rapel_value = temp_penerimaan - temp_rapel
                # cek jika ada proporsi khusus THR
                if old.is_proportion:
                    rapel_value *= eval(old.proportion_value)

                payroll_employee.rapel += rapel_value
                self.env['ka_hr_payroll.payroll.employee.rapel'].create({
                    'payroll_rapel_pay_id': payroll_employee.id,
                    'payroll_rapel_ref_id': old.id,
                    'payroll_rapel_value': rapel_value,
                })

            # cari data payroll afkoop
            old_afkoop_employee = self.env['ka_hr.holidays.afkoop'].search([
                ('employee_id', '=', self.id),
                ('date_approve', '>=', date_start),
                ('date_approve', '<=', date_end),
                ('state', '=', 'approved'),
            ])

            for old in old_afkoop_employee:
                temp_penerimaan = payroll_employee.gapok_total
                # cek old afkoop, penghitungan selisih bukan dari payroll_employee.total_pre_rapel
                # misal di afkoop tidak ada tunjangan_rumah, jd penghitungannya payroll_employee jg tanpa tunj_rumah.
                if old.is_tunjangan_rumah:
                    temp_penerimaan += payroll_employee.tunjangan_rumah
                if old.is_tunjangan_jabatan:
                    temp_penerimaan += payroll_employee.tunjangan_jabatan
                if old.is_tunjangan_khusus:
                    temp_penerimaan += payroll_employee.tunjangan_khusus
                if old.is_tunjangan_representasi:
                    temp_penerimaan += payroll_employee.tunjangan_representasi

                # dimultiply tergantung dari multiply afkoop
                temp_penerimaan *= int(old.jumlah)

                # cek tambahan total_penerimaan, karena bisa jadi sudah ada rapel pada bulan itu
                afkoop_rapel = self.env['ka_hr_payroll.payroll.afkoop.rapel'].search([
                    ('afkoop_rapel_ref_id', '=', old.id),
                ])

                temp_rapel = old.total_multiply
                for ar in afkoop_rapel:
                    temp_rapel += ar.afkoop_rapel_value

                rapel_value = temp_penerimaan - temp_rapel
                payroll_employee.rapel += rapel_value
                self.env['ka_hr_payroll.payroll.afkoop.rapel'].create({
                    'payroll_rapel_pay_id': payroll_employee.id,
                    'afkoop_rapel_ref_id': old.id,
                    'afkoop_rapel_value': rapel_value,
                })

            # cari data payroll tunjangan cuti
            old_tunjangan_holidays = self.env['ka_hr_payroll.tunjangan.holidays'].search([
                ('holiday_employee_id', '=', self.id),
                ('date_approve', '>=', date_start),
                ('date_approve', '<=', date_end),
                ('state', '=', 'approved')
            ])

            for old in old_tunjangan_holidays:
                temp_penerimaan = payroll_employee.gapok_total
                # cek old afkoop, penghitungan selisih bukan dari payroll_employee.total_pre_rapel
                # misal di afkoop tidak ada tunjangan_rumah, jd penghitungannya payroll_employee jg tanpa tunj_rumah.
                if old.is_tunjangan_rumah:
                    temp_penerimaan += payroll_employee.tunjangan_rumah
                if old.is_tunjangan_jabatan:
                    temp_penerimaan += payroll_employee.tunjangan_jabatan
                if old.is_tunjangan_khusus:
                    temp_penerimaan += payroll_employee.tunjangan_khusus
                if old.is_tunjangan_representasi:
                    temp_penerimaan += payroll_employee.tunjangan_representasi

                # Kalikan nilai pengali
                temp_penerimaan *= old.multiply_value

                # cek tambahan total_penerimaan, karena bisa jadi sudah ada rapel pada bulan itu
                tunj_rapel = self.env['ka_hr_payroll.payroll.tunjangan.holidays.rapel'].search([
                    ('tunjangan_holidays_rapel_ref_id', '=', old.id),
                ])

                temp_rapel = old.total
                for tr in tunj_rapel:
                    temp_rapel += tr.tunjangan_holidays_rapel_value

                rapel_value = temp_penerimaan - temp_rapel
                payroll_employee.rapel += rapel_value
                self.env['ka_hr_payroll.payroll.tunjangan.holidays.rapel'].create({
                    'payroll_rapel_pay_id': payroll_employee.id,
                    'tunjangan_holidays_rapel_ref_id': old.id,
                    'tunjangan_holidays_rapel_value': rapel_value,
                })

            # cari data payroll reward
            old_employee_reward = self.env['ka_hr_payroll.employee.reward'].search([
                ('employee_id', '=', self.id),
                ('date_approve', '>=', date_start),
                ('date_approve', '<=', date_end),
                ('state', '=', 'approved'),
                ('reward_type', '=', '1'),
            ])

            for old in old_employee_reward:
                temp_penerimaan = payroll_employee.gapok_total
                # cek old afkoop, penghitungan selisih bukan dari payroll_employee.total_pre_rapel
                # misal di afkoop tidak ada tunjangan_rumah, jd penghitungannya payroll_employee jg tanpa tunj_rumah.
                if old.is_tunjangan_rumah:
                    temp_penerimaan += payroll_employee.tunjangan_rumah
                if old.is_tunjangan_jabatan:
                    temp_penerimaan += payroll_employee.tunjangan_jabatan
                if old.is_tunjangan_khusus:
                    temp_penerimaan += payroll_employee.tunjangan_khusus
                if old.is_tunjangan_representasi:
                    temp_penerimaan += payroll_employee.tunjangan_representasi

                # Kalikan nilai pengali
                temp_penerimaan *= old.multiply_value

                employee_reward_rapel = self.env['ka_hr_payroll.payroll.employee.reward.rapel'].search([
                    ('employee_reward_rapel_ref_id', '=', old.id),
                ])

                temp_rapel = old.total
                for er in employee_reward_rapel:
                    temp_rapel += er.employee_reward_rapel_value

                rapel_value = temp_penerimaan - temp_rapel
                payroll_employee.rapel += rapel_value
                self.env['ka_hr_payroll.payroll.employee.reward.rapel'].create({
                    'payroll_rapel_pay_id': payroll_employee.id,
                    'employee_reward_rapel_ref_id': old.id,
                    'employee_reward_rapel_value': rapel_value,
                })

    def _generate_potongan(self, last_konjungtur_dapen, payroll_employee):
        for potongan in self.potongan_ids:
            value = 0.0

            parent = potongan.potongan_id
            pokok = self.gaji_pokok
            if parent.type_potongan == '1':
                # type prosentase
                if potongan.is_multiply_konjungtur:
                    if potongan.konjungtur_type == '1':
                        # multiply konjungtur gaji
                        pokok = payroll_employee.gapok_total
                    else:
                        # multiply konjungtur dapen
                        pokok *= (last_konjungtur_dapen.value / 100)

                value = pokok * (parent.prosentase / 100)
                if parent.is_max_value:
                    # has max value
                    if value > parent.max_value:
                        value = parent.max_value
            elif parent.type_potongan == '2':
                # type fix value
                value = parent.fixed_value

            self.env['ka_hr_payroll.payroll.employee.potongan.lines'].create({
                'payroll_employee_id': payroll_employee.id,
                'potongan_id': parent.id,
                'value': round(value),
            })

    def generate_holidays(self, holiday_date):
        """Override.
        To generate holidays allocation based on employee.

		Arguments:
			holiday {Recordset} -- ID of `hr.holidays`.
			holiday_date {Date} -- Date of holidays.
		"""
        new_allocation = super(KaHrPayrollEmployee, self).generate_holidays(holiday_date)
        if new_allocation.is_create_tunjangan:
            self.generate_tunjangan_holidays(new_allocation)

    def generate_tunjangan_holidays(self, new_allocation):
        """To generate tunjangan holidays based on holiday.

        Arguments:
            holiday {Recordset} -- ID of `hr.holidays`.
        """
        tunjangan = self.env['ka_hr_payroll.tunjangan.holidays'].create({
            'holiday_id': new_allocation.id,
            'date_tunjangan': new_allocation.date_start,
            'holiday_employee_id': self.id,
            'company_payroll_id': self.company_payroll_id.id,
        })
        # tunjangan.action_process()
        new_allocation.tunjangan_holiday_id = tunjangan

    @api.multi
    def action_view_payroll(self):
        """To view `ka_hr_payroll.payroll.employee` related with this employee.

        Returns:
            Dict -- Action result to view list of payroll.
        """
        # action = self.env.ref('ka_hr_payroll.action_payroll_per_employee')
        action = self.env.ref('ka_hr_payroll.action_payroll_employee')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result

    @api.multi
    def action_view_tunjangan_holidays(self):
        """To view `ka_hr_payroll.tunjangan.holidays` related with this employee.

        Returns:
            Dict -- Action result to view list of tunjangan holidays.
        """
        action = self.env.ref('ka_hr_payroll.action_tunjangan_holidays')
        result = action.read()[0]
        result['domain'] = [('holiday_employee_id', '=', self.id)]
        result['context'] = {'default_holiday_employee_id': self.id}
        return result

    @api.multi
    def action_view_afkoop(self):
        action = self.env.ref('ka_hr_holidays.action_view_holidays_afkoop')
        result = action.read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        result['context'] = {'default_employee_id': self.id}
        return result
