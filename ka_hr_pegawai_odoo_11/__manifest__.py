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

    'author': "Cak Juice",
    'website': "https://cakjuice.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['ka_base', 'ka_base_wilayah', 'hr', 'document', 'web_notify'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'reports/employee_sp.xml',

        'views/templates.xml',
        'views/hr_department.xml',
        'views/hr_jabatan.xml',
        'views/hr_pangkat.xml',
        'views/hr_golongan.xml',
        'views/hr_status.xml',
        'views/res_users.xml',
        'views/res_company.xml',
        'views/hr_employee.xml',
        'views/hr_employee_promote.xml',
        'views/hr_employee_sp.xml',
        'views/hr_document_legal.xml',
        'views/hr_document_asset.xml',
        'views/hr_document_kerjasama.xml',

        'wizards/employee_config.xml',

        'data/data_hr_jabatan.xml',
        'data/data_hr_pangkat.xml',
        'data/data_hr_golongan.xml',
        'data/data_hr_status.xml',
        'data/data_hr_config.xml',
        'data/data_ir_sequence.xml',
        'data/ir_cron_check_employee_daily.xml',
        'data/template_mail_employee_sp_approved.xml',
        'data/template_mail_employee_sp_canceled.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
