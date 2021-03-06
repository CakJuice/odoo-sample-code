# -*- coding: utf-8 -*-
{
    'name': "SDM - Kepegawaian",

    'summary': """
        Pegawai, Departemen, Jabatan, category - PT. Kebon Agung""",

    'description': """
        Simple Pengelolaan Pegawai:\n
        * Pegawai\n
        * Departemen\n
        * Jabatan\n
        * Kategori\n
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr',
        'document',
        'ka_base_wilayah',
        'ka_report_layout',
        'web_notify',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/hr_security.xml',

        'wizards/employee_config.xml',
        # 'wizards/employee_create.xml',

        'reports/employee_sp.xml',

        'views/templates.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/hr_document.xml',
        'views/res_company.xml',
        # 'views/hr_job.xml',
        'views/hr_employee_sp.xml',
        'views/hr_jabatan.xml',
        'views/hr_pangkat.xml',
        'views/hr_golongan.xml',
        'views/hr_status.xml',
        'views/hr_employee_promote.xml',

        'helpers/cleaning_field.xml',

        'data/ir_sequence.xml',
        'data/template_mail_employee_sp_approved.xml',
        'data/template_mail_employee_sp_canceled.xml',
        'data/data_hr_jabatan.xml',
        'data/data_hr_pangkat.xml',
        'data/data_hr_golongan.xml',
        'data/data_hr_status.xml',
        'data/data_hr_config.xml',
        # 'data/ir_cron_employee_check_daily.xml',
    ],
}