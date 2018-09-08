# -*- coding: utf-8 -*-
{
    'name': "SDM - Penggajian (Payroll)",

    'summary': """
        Modul penggajian karyawan""",

    'description': """
        Pengelolaan data penggajian karyawan
    """,

    'author': "PT. Kebon Agung",
    'website': "http://ptkebonagung.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'ka_hr_pegawai',
        'ka_hr_attendance',
        'ka_account',
        'web_notify',
        'report_qweb_element_page_visibility'
    ],

    # always loaded
    'data': [
        'security/ka_hr_payroll.xml',
        'security/ir.model.access.csv',

        'reports/paperformat_slip.xml',
        'reports/paperformat_slip_income.xml',
        'reports/payroll_slip_report.xml',
        'reports/payroll_thr_slip_report.xml',
        'reports/payroll_recap_report.xml',
        'reports/tunjangan_holidays_slip_report.xml',
        'reports/holidays_afkoop_slip_report.xml',
        'reports/employee_reward_slip_report.xml',
        'reports/employee_dinas_slip_report.xml',

        'views/templates.xml',
        'views/company_konjungtur.xml',
        'views/rapel_company_konjungtur.xml',
        'views/res_company.xml',
        'views/hr_status.xml',
        'views/hr_employee.xml',
        'views/company_periodic_promote.xml',
        'views/hr_employee_promote.xml',
        'views/rapel_employee_promote.xml',
        'views/scale.xml',
        'views/rapel_scale.xml',
        'views/tunjangan_khusus.xml',
        'views/rapel_tunjangan_khusus.xml',
        'views/tunjangan_representasi.xml',
        'views/rapel_tunjangan_representasi.xml',
        'views/potongan.xml',
        'views/company_default.xml',
        'views/rapel_company_default.xml',
        'views/payroll.xml',
        'views/holidays_afkoop.xml',
        'views/tunjangan_holidays.xml',
        'views/employee_holidays.xml',
        'views/reward.xml',
        'views/employee_reward.xml',
        'views/dinas.xml',
        'views/employee_dinas.xml',

        'wizards/payroll_config.xml',
        'wizards/payroll_company_config.xml',
        'wizards/payroll_slip_report.xml',
        'wizards/payroll_recap_report.xml',

        'data/data_config.xml',
        'data/data_reward.xml',
        'data/data_potongan.xml',
        'data/data_dinas_master.xml',
        'data/template_mail_tunjangan_holidays.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}