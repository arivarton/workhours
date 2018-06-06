import os
import sys
import calendar
import operator

from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from .settings import (REPORT_DIR, ORG_NR, FILE_DIR, COMPANY_NAME, COMPANY_ADDRESS,
                       COMPANY_ZIP_CODE, COMPANY_ACCOUNT_NUMBER, MAIL, PHONE)
from .db import get_one_db_entry, query_db_export_filter
from .exceptions import TooManyMatchesError, ArgumentError, NoMatchingDatabaseEntryError
from .helpers import output_for_total_hours_date_and_wage


def _parse_export_filter(selected_month, selected_year, selected_customer=None,
                         selected_project=None):
    export_filter = dict()
    # Validate month
    _valid_months = ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November',
                     'December']
    _selected_month = list()
    for month in _valid_months:
        if month.startswith(selected_month.capitalize()):
            _selected_month.append(month)
    if len(_selected_month) > 1:
        raise TooManyMatchesError('Refine month argument! These months are currently matching: %s.' %
                                  ', '.join(_selected_month))
    selected_month = ''.join(_selected_month)

    # Validate year
    try:
        date_from = datetime.strptime('%s %s' % (selected_month, selected_year),
                                      '%B %Y')
        _month_days = calendar.monthrange(date_from.year, date_from.month)[1]
        date_to = date_from + timedelta(days=_month_days)
    except ValueError:
        raise ArgumentError('Year argument format wrong! This is the correct format: YYYY. For example: 2018.')

    export_filter.update({'start': {'op_func': operator.ge, 'value': date_from},
                          'end': {'op_func': operator.lt, 'value': date_to}})

    # Validate customer
    if selected_customer:
        try:
            selected_customer = get_one_db_entry('Customer', 'name', selected_customer)
        except NoMatchingDatabaseEntryError as _err_msg:
            print(_err_msg)
            sys.exit(0)
        export_filter.update({'customer_id': {'op_func': operator.eq,
                                              'value': selected_customer.id}})

    # Validate project
    if selected_project:
        try:
            selected_project = get_one_db_entry('Project', 'name', selected_project)
        except NoMatchingDatabaseEntryError as _err_msg:
            print(_err_msg)
            sys.exit(0)
        export_filter.update({'project_id': {'op_func': operator.eq,
                                             'value': selected_project.id}})

    return export_filter


def create_pdf(args):
    export_filter = _parse_export_filter(args.month, args.year, args.customer,
                                         args.project)
    try:
        workdays = query_db_export_filter('Workday', export_filter)
    except NoMatchingDatabaseEntryError as _err_msg:
        print(_err_msg)
        sys.exit(0)

    output_filename = os.path.join(REPORT_DIR, 'report.pdf')

    # Document settings
    PAGE_HEIGHT = A4[1]
    PAGE_WIDTH = A4[0]
    logo_file = os.path.join(FILE_DIR, 'logo.png')
    invoice_date = datetime.now()
    maturity_date = datetime.now() + timedelta(days=60)
    delivery_date = datetime.now()
    company_info_start_height = PAGE_HEIGHT - 20
    company_info_start_width = 50
    company_info2_start_height = PAGE_HEIGHT - 130
    company_info2_start_width = 50
    invoice_start_height = 130
    invoice_start_width = PAGE_WIDTH - 150
    bottom_start_width = 18
    bottom_end_width = PAGE_WIDTH - 108
    bottom_start_height = 18

    def myFirstPage(canvas, doc):
        output_hours, output_date, output_wage = output_for_total_hours_date_and_wage(workdays)
        canvas.saveState()
        if os.path.isfile(logo_file):
            canvas.drawImage(logo_file, PAGE_WIDTH - 60, company_info_start_height - 30, width=40, height=40, mask=[0, 0, 0, 0, 0, 0],
                             preserveAspectRatio=True)

        # Sellers company info
        canvas.setFont('Times-Bold', 12)
        canvas.drawString(company_info_start_width, company_info_start_height, COMPANY_NAME)
        canvas.setFont('Times-Bold', 9)
        canvas.drawString(company_info_start_width, company_info_start_height - 37, "Org nr:")
        canvas.drawString(company_info_start_width, company_info_start_height - 48, "Epost:")
        canvas.drawString(company_info_start_width, company_info_start_height - 59, "Tlf:")
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(company_info_start_width, company_info_start_height - 10, COMPANY_ADDRESS)
        canvas.drawString(company_info_start_width, company_info_start_height - 21, COMPANY_ZIP_CODE)
        canvas.drawString(company_info_start_width + 50, company_info_start_height - 37, ORG_NR)
        canvas.drawString(company_info_start_width + 50, company_info_start_height - 48, MAIL)
        canvas.drawString(company_info_start_width + 50, company_info_start_height - 59, PHONE)

        # Buyers company info
        canvas.setFont('Times-Bold', 12)
        canvas.drawString(company_info2_start_width, company_info2_start_height,
                          workdays[0].customer.name)
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(company_info2_start_width, company_info2_start_height - 10, 'Klepp stasjon')
        canvas.drawString(company_info2_start_width, company_info2_start_height - 21, '4353')

        # Invoice
        canvas.setFont('Times-Bold', 14)
        canvas.drawString(invoice_start_width, PAGE_HEIGHT-invoice_start_height, "Faktura")
        canvas.setFont('Times-Bold', 9)
        canvas.drawString(invoice_start_width, PAGE_HEIGHT-(invoice_start_height + 15), "Kunde nr:")
        canvas.drawString(invoice_start_width, PAGE_HEIGHT-(invoice_start_height + 26), "Faktura nr:")
        canvas.drawString(invoice_start_width, PAGE_HEIGHT-(invoice_start_height + 37), "Faktura dato:")
        canvas.drawString(invoice_start_width, PAGE_HEIGHT-(invoice_start_height + 48), "Forfalls dato:")
        canvas.drawString(invoice_start_width, PAGE_HEIGHT-(invoice_start_height + 59), "Leverings dato:")
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(invoice_start_width + 80, PAGE_HEIGHT-(invoice_start_height + 15), "01")
        canvas.drawString(invoice_start_width + 80, PAGE_HEIGHT-(invoice_start_height + 26), "01")
        canvas.drawString(invoice_start_width + 80, PAGE_HEIGHT-(invoice_start_height + 37), invoice_date.strftime('%d.%m.%Y'))
        canvas.drawString(invoice_start_width + 80, PAGE_HEIGHT-(invoice_start_height + 48), maturity_date.strftime('%d.%m.%Y'))
        canvas.drawString(invoice_start_width + 80, PAGE_HEIGHT-(invoice_start_height + 59), delivery_date.strftime('%d.%m.%Y'))

        # Bottom info
        canvas.setFont('Times-Roman', 9)
        canvas.drawCentredString(PAGE_WIDTH/2.0, bottom_start_height, output_wage)
        canvas.drawString(bottom_start_width, bottom_start_height, COMPANY_NAME)
        canvas.drawString(bottom_end_width, bottom_start_height, COMPANY_ACCOUNT_NUMBER)

        canvas.restoreState()

    def myLaterPages(canvas, doc):
        output_hours, output_date, output_wage = output_for_total_hours_date_and_wage(workdays)
        canvas.saveState()
        # Bottom info
        canvas.setFont('Times-Roman', 9)
        canvas.drawCentredString(PAGE_WIDTH/2.0, bottom_start_height, output_wage)
        canvas.drawString(bottom_start_width, bottom_start_height, COMPANY_NAME)
        canvas.drawString(bottom_end_width, bottom_start_height, COMPANY_ACCOUNT_NUMBER)
        canvas.restoreState()

    doc = SimpleDocTemplate(output_filename)
    Story = [Spacer(1, 2*inch)]
    workday_info = [['Dato', 'Fra', 'Til', 'Timer', 'Lønn']]
    for workday in workdays:
        output_hours, output_date, output_wage = output_for_total_hours_date_and_wage(workday)
        workday_info.append([output_date,
                             workday.start.time().strftime('%H:%M'),
                             workday.end.time().strftime('%H:%M'),
                             output_hours,
                             output_wage])
    t = Table(workday_info, colWidths=100, style=[
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold')]
    )
    Story.append(t)
    doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)

    return
