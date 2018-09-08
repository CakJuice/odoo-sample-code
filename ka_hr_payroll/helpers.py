# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

MONTH_LIST = [
    (1, "Januari"),
    (2, "Pebruari"),
    (3, "Maret"),
    (4, "April"),
    (5, "Mei"),
    (6, "Juni"),
    (7, "Juli"),
    (8, "Agustus"),
    (9, "September"),
    (10, "Oktober"),
    (11, "Nopember"),
    (12, "Desember"),
]

YEAR_LIST = [(i, str(i)) for i in range(datetime.now().year - 2, datetime.now().year + 1)]

def get_utc_timezone(jakarta_timezone):
    """Convert jakarta timezone to utc timezone.

    Arguments:
        jakarta_timezone {String|Datetime} -- Datetime or String of jakarta timezone.

    Returns:
        String -- UTC timezone in String type.
    """
    if isinstance(jakarta_timezone, basestring):
        jt_obj = datetime.strptime(jakarta_timezone, DATETIME_FORMAT)
        utc_timezone = jt_obj - timedelta(hours=7)
    else:
        utc_timezone = jakarta_timezone - timedelta(hours=7)

    return utc_timezone.strftime(DATETIME_FORMAT)

def get_jakarta_timezone(utc_timezone):
    """Convert utc timezone to jakarta timezone.

    Arguments:
        utc_timezone {String|Datetime} -- Datetime or String of utc timezone.

    Returns:
        String -- Jakarta timezone in String type.
    """
    if isinstance(utc_timezone, basestring):
        utc_obj = datetime.strptime(utc_timezone, DATETIME_FORMAT)
        utc_timezone = utc_obj + timedelta(hours=7)
    else:
        utc_timezone = utc_timezone + timedelta(hours=7)

    return utc_timezone.strftime(DATETIME_FORMAT)

def check_rapel_status(obj, config, is_recruitment=False, is_extended=False):
    """To check 'penerimaan' (like scale & tunjangan) is must have rapel or not.

    Arguments:
        obj {Recordset} -- Record of penerimaan.
        config {Recordset} -- Result from `ka_hr_payroll.config` `default_config()`.

    Returns:
        Boolean -- Result of obj is should have rapel or not.
    """
    date_approve = datetime.strptime(get_jakarta_timezone(obj.date_approve), DATETIME_FORMAT)
    date_start = datetime.strptime(obj.date_start, DATE_FORMAT)

    if is_recruitment or is_extended:
        return False

    diff = date_approve - date_start
    if diff.days <= 0:
        return False

    if date_approve.month != date_start.month or date_approve.year != date_start.year:
        return True
    elif date_approve.month == date_start.month and date_approve.year == date_start.year:
        if date_approve.day > config.date_end:
            return True
    return False

def datetime_to_local_date(datetime_str):
    """Convert string of datetime to local (indonesian) string of date.

    Arguments:
        datetime_str {String} -- String of datetime.

    Returns:
        String -- Convert result, string of date.
    """
    date_obj = datetime.strptime(datetime_str, DATETIME_FORMAT).date()
    return date_obj.strftime('%d-%m-%Y')

def date_to_local_date(date_str):
    """Convert string of date to local (indonesian) string of date.

    Arguments:
        date_str {String} -- String of date.

    Returns:
        String -- Convert result, string of date.
    """
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    return date_obj.strftime('%d-%m-%Y')

def format_local_currency(value):
    """Convert from float currency to local (indonesian) string of currency.

    Arguments:
        value {Float} -- Value wants to change.

    Returns:
        String -- Convert result, string of currency.
    """
    new_format = '{0:,.0f}'.format(value)
    return new_format.replace(',', ';').replace('.', ',').replace(';', '.')
