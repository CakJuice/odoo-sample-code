# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class hr_employee_graduate(models.Model):
	"""Data of employee graduation.

	_name = 'hr.employee.graduate'
	"""

	_name = 'hr.employee.graduate'
	_description = "SDM Riwayat Pendidikan Pegawai"

	employee_id = fields.Many2one('hr.employee', string='Pegawai', required=True)
	graduate_type = fields.Selection([
		('sma', "SMA/Sederajat"),
		('d3', 'Diploma III'),
		('s1', "Strata I"),
		('s2', "Strata II"),
		('s3', "Strata III")
	], string="Jenis Pendidikan", required=True)
	lembaga = fields.Char(string='Lembaga', size=32)
	jurusan = fields.Char(string='Jurusan', size=32)
	tahun = fields.Char(string='Tahun', size=4)

class hr_employee_course(models.Model):
	"""Data of employee course.

	_name = 'hr.employee.course'
	"""

	_name = 'hr.employee.course'
	_description = "SDM Riwayat Pendidikan Non Formal"

	employee_id = fields.Many2one('hr.employee', string='Pegawai', required=True)
	lembaga = fields.Char(string='Lembaga', size=32)
	keterangan = fields.Char(string='Uraian/Materi', size=256)
	tahun = fields.Char(string='Tahun', size=4)
