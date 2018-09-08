# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError

from ..helpers import MONTH_LIST, YEAR_LIST, format_local_currency


class KaHrPayrollRecapReportWizard(models.TransientModel):
    """Wizard used to create payroll recap report.

    _name = 'ka_hr_payroll.recap.report.wizard'
    """

    _name = 'ka_hr_payroll.recap.report.wizard'

    year_period = fields.Selection(YEAR_LIST, string="Tahun Periode", required=True,
                                   default=datetime.now().year)
    month_period = fields.Selection(MONTH_LIST, string="Bulan Periode", required=True,
                                    default=datetime.now().month)
    status_id = fields.Many2one('hr.status', string="Status Karyawan", required=True,
                                domain=[('parent_id', '=', None)])
    company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
                                 default=lambda self: self.env.user.company_id)
    company_payroll_id = fields.Many2one('res.company', string="Lokasi Penggajian", required=True,
                                         default=lambda self: self.env.user.company_id)

    @api.multi
    def generate_report(self):
        """To generate report. Call from button.
        """
        report_obj = self.env['report']
        template = 'ka_hr_payroll.payroll_recap_report_view'
        report = report_obj._get_report_from_name(template)

        payroll = self.env['ka_hr_payroll.payroll'].search([
            ('year_period', '=', self.year_period),
            ('month_period', '=', self.month_period),
            ('employee_status_id', '=', self.status_id.id),
        ], limit=1)

        if not payroll:
            raise ValidationError("Data penggajian tidak ditemukan!")

        form = {
            'year_period': self.year_period,
            'month_period': self.month_period,
            'status_id': self.status_id.id,
            'company_id': self.company_id.id,
            'company_payroll_id': self.company_payroll_id.id,
        }
        data = {
            'ids': self.ids,
            'model': report.model,
            'form': form,
        }
        return report_obj.get_action(self, template, data=data)


class ReportKaHrPayrollRecapReport(models.AbstractModel):
    """Abstract model to create payroll recap report.

    _name = 'report.ka_hr_payroll.payroll_recap_report_view'
    """

    _name = 'report.ka_hr_payroll.payroll_recap_report_view'
    _TEMPLATE = 'ka_hr_payroll.payroll_recap_report_view'

    _MONTH_NAME = ["Januari", "Pebruari", "Maret", "April",
                   "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "Nopember", "Desember"]

    def formatting_currency(self, value):
        """To convert currency format from float to Indonesian currency.

        Arguments:
            value {Float} -- Value which want to change.

        Returns:
            String -- Value string formatted.
        """
        return format_local_currency(value)

    def _get_default_total(self):
        return {
            'gapok': 0,
            'gapok_total': 0,
            'tunjangan_rumah': 0,
            'tunjangan_jabatan': 0,
            'tunjangan_khusus': 0,
            'tunjangan_representasi': 0,
            'rapel': 0,
            'total_penerimaan': 0,
            'total_potongan': 0,
            'total': 0,
            'potongan': []
        }

    def _appending_data(self, data):
        return {
            'name': data.employee_id.name,
            'gapok': data.gaji_pokok,
            'gapok_total': data.gapok_total,
            'is_multiply_konjungtur': data.is_multiply_konjungtur,
            'tunjangan_rumah': data.tunjangan_rumah,
            'tunjangan_jabatan': data.tunjangan_jabatan,
            'tunjangan_khusus': data.tunjangan_khusus,
            'tunjangan_representasi': data.tunjangan_representasi,
            'rapel': data.rapel,
            'total_penerimaan': data.total_penerimaan,
            'total_potongan': data.total_potongan,
            'total': data.total,
            'potongan': [],
        }

    def get_recap_direksi(self):
        """Get recap data, if is_direksi = `True`.
        Data result example:
        [{
            'gapok': 33750000.0,
            'gapok_total': 33750000.0,
            'is_multiply_konjungtur': False,
            'name': u'EDI SISWANTO',
            'potongan': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'rapel': 0.0,
            'total': 33750000.0,
            'total_penerimaan': 33750000.0,
            'total_potongan': 0.0,
            'tunjangan_jabatan': 0.0,
            'tunjangan_khusus': 0.0,
            'tunjangan_representasi': 0.0,
            'tunjangan_rumah': 0.0
        },]

        Returns:
            Tuple -- Data recap & total recap.
        """
        data = []
        total = self._get_default_total()

        employee_payroll = self.payroll.payroll_employee_ids.filtered(
            lambda r: r.employee_id.company_id.id == self.company_id)
        employee_filter = employee_payroll.sorted(lambda r: r.employee_id.status_id.id)

        for ef in employee_filter:
            new_data = self._appending_data(ef)
            data.append(new_data)

            total['gapok'] += new_data.get('gapok', 0)
            total['gapok_total'] += new_data.get('gapok_total', 0)
            total['tunjangan_rumah'] += new_data.get('tunjangan_rumah', 0)
            total['tunjangan_jabatan'] += new_data.get('tunjangan_jabatan', 0)
            total['tunjangan_khusus'] += new_data.get('tunjangan_khusus', 0)
            total['tunjangan_representasi'] += new_data.get('tunjangan_representasi', 0)
            total['rapel'] += new_data.get('rapel', 0)
            total['total_penerimaan'] += new_data.get('total_penerimaan', 0)

            data_potongan = data[-1].get('potongan')
            idx_pot = 0
            for pot in self.potongan:
                pot_lines = self.env['ka_hr_payroll.payroll.employee.potongan.lines'].search([
                    ('payroll_employee_id', '=', ef.id),
                    ('potongan_id', '=', pot.id),
                ], limit=1)
                if pot_lines:
                    pot_value = pot_lines.value
                else:
                    pot_value = 0.0
                data_potongan.append(pot_value)

                if total['potongan']:
                    if len(total['potongan']) <= idx_pot:
                        total['potongan'].append(pot_value)
                    else:
                        total['potongan'][idx_pot] += pot_value
                else:
                    total['potongan'].append(pot_value)

                idx_pot += 1

        return data, total

    def get_recap_non_direksi(self):
        """Get recap data, if is_direksi = `True`.
        Data result example:
        [{
            'department': u'SATUAN PENGAWASAN INTERN / SPI',
            'payroll': [
                {
                    'gapok': 10003875.0,
                    'gapok_total': 20187819.75,
                    'is_multiply_konjungtur': True,
                    'name': u'SABUR HARIANTO, DRS. EC.',
                    'potongan': [
                        403757.0,
                        524884.0,
                        242820.0,
                        236250.0,
                        833773.0,
                        0.0
                    ],
                    'rapel': 0.0,
                    'total': 33050778.75,
                    'total_penerimaan': 35292262.75,
                    'total_potongan': 2241484.0,
                    'tunjangan_jabatan': 2947423.0,
                    'tunjangan_khusus': 7171000.0,
                    'tunjangan_representasi': 2500000.0,
                    'tunjangan_rumah': 2486020.0
                },
            'sub_total': {
                'gapok': 31591875.0,
                'gapok_total': 63752403.75,
                'potongan': [
                    1275051.0,
                    1657565.0,
                    1214100.0,
                    1181250.0,
                    2633027.0,
                    0.0
                ],
                'rapel': 0.0,
                'total': 0,
                'total_penerimaan': 106473162.74999999,
                'total_potongan': 0,
                'tunjangan_jabatan': 9308679.0,
                'tunjangan_khusus': 23055000.0,
                'tunjangan_representasi': 2500000.0,
                'tunjangan_rumah': 7857080.0
            }
        }]

        Returns:
            Tuple -- Data recap & total recap.
        """
        data = []
        total = self._get_default_total()

        employee_payroll = self.payroll.payroll_employee_ids.filtered(
            lambda r: r.employee_id.company_id.id == self.company_id)

        departments = self.env['hr.department'].search([
            ('company_id', '=', self.company_id)
        ], order='id asc')

        for department in departments:
            employee_filter = employee_payroll.filtered(lambda r: r.employee_id.department_id == department)
            employee_filter = employee_filter.sorted(lambda r: r.employee_id.jabatan_id.id)

            data.append({
                'department': department.name,
                'payroll': [],
                'sub_total': {}
            })

            sub_total = self._get_default_total()

            for ef in employee_filter:
                data_payroll = data[-1].get('payroll')
                data_payroll.append(self._appending_data(ef))

                sub_total['gapok'] += ef.gaji_pokok
                sub_total['gapok_total'] += ef.gapok_total
                sub_total['tunjangan_rumah'] += ef.tunjangan_rumah
                sub_total['tunjangan_jabatan'] += ef.tunjangan_jabatan
                sub_total['tunjangan_khusus'] += ef.tunjangan_khusus
                sub_total['tunjangan_representasi'] += ef.tunjangan_representasi
                sub_total['rapel'] += ef.rapel
                sub_total['total_penerimaan'] += ef.total_penerimaan

                data_potongan = data_payroll[-1].get('potongan')
                idx_pot = 0
                for pot in self.potongan:
                    pot_lines = self.env['ka_hr_payroll.payroll.employee.potongan.lines'].search([
                        ('payroll_employee_id', '=', ef.id),
                        ('potongan_id', '=', pot.id),
                    ], limit=1)
                    if pot_lines:
                        pot_value = pot_lines.value
                    else:
                        pot_value = 0.0
                    data_potongan.append(pot_value)

                    if sub_total['potongan']:
                        if len(sub_total['potongan']) <= idx_pot:
                            sub_total['potongan'].append(pot_value)
                        else:
                            sub_total['potongan'][idx_pot] += pot_value
                    else:
                        sub_total['potongan'].append(pot_value)

                    if total['potongan']:
                        if len(total['potongan']) <= idx_pot:
                            total['potongan'].append(pot_value)
                        else:
                            total['potongan'][idx_pot] += pot_value
                    else:
                        total['potongan'].append(pot_value)

                    idx_pot += 1

            data[-1]['sub_total'] = sub_total

            total['gapok'] += sub_total.get('gapok', 0)
            total['gapok_total'] += sub_total.get('gapok_total', 0)
            total['tunjangan_rumah'] += sub_total.get('tunjangan_rumah', 0)
            total['tunjangan_jabatan'] += sub_total.get('tunjangan_jabatan', 0)
            total['tunjangan_khusus'] += sub_total.get('tunjangan_khusus', 0)
            total['tunjangan_representasi'] += sub_total.get('tunjangan_representasi', 0)
            total['rapel'] += sub_total.get('rapel', 0)
            total['total_penerimaan'] += sub_total.get('total_penerimaan', 0)

        return data, total

    def render_html(self, docids, data=None):
        """Override method. To render report in html.
        Called automatically from `ir.actions.report.xml`.

        Arguments:
            docids -- {Int} ID of document report.
            data -- {Dict} Data of report. Used when no docids,
        """
        report_obj = self.env['report']
        form = data.get('form')

        year_period = form.get('year_period')
        month_period = form.get('month_period')
        status_id = form.get('status_id')

        self.payroll = self.env['ka_hr_payroll.payroll'].search([
            ('year_period', '=', year_period),
            ('month_period', '=', month_period),
            ('employee_status_id', '=', status_id),
        ], limit=1)

        self.company_id = form.get('company_id')
        company_payroll_id = form.get('company_payroll_id')

        periode_name = "{} {}".format(self._MONTH_NAME[month_period - 1], year_period)
        self.potongan = self.env['ka_hr_payroll.potongan'].search([
            ('is_mandatory', '=', True),
            ('company_payroll_id', '=', company_payroll_id),
        ])

        company = self.env['res.company'].browse(self.company_id)
        hr_config = self.env['hr.config'].default_config()
        is_direksi = False
        if status_id == hr_config.hr_status_direksi_id.id:
            is_direksi = True
            data_recap = self.get_recap_direksi()
        else:
            data_recap = self.get_recap_non_direksi()

        docs = data_recap[0]
        total = data_recap[1]

        values = {
            'periode_name': periode_name,
            'potongan': [pot.name for pot in self.potongan],
            'company_name': company.name or '',
            'docs': docs,
            'total': total,
            'is_direksi': is_direksi,
            'model': self,
        }

        return report_obj.render(self._TEMPLATE, values=values)
