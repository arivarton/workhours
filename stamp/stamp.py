#!/usr/bin/env python3

##############################
#
#    Stamp in before starting
#    the workday, tag
#    points in time with
#    comments and stamp out
#    when workday is over.
#
##############################


from datetime import datetime
import argparse
import re
import sys
import os

from . import __version__
from .settings import STANDARD_CUSTOMER, STANDARD_PROJECT, DATA_DIR, DB_FILE
from .add import stamp_in, create_invoice
from .end import stamp_out
from .edit import edit_regex_resolver, edit_workday
from .status import print_status, print_current_stamp
from .delete import delete_workday_or_tag
from .tag import tag_stamp
from .db import query_for_workdays, current_stamp, query_db_export_filter
from .export import parse_export_filter
from .exceptions import NoMatchingDatabaseEntryError
from .pprint import yes_or_no


def _get_value_from_time_parameter(time):
    # Separate each part of time that user has put as argument
    # Argument could f.ex. look like this: 16:45
    hours, minutes = re.findall(r"[0-9]+", time)
    try:
        return datetime.time(datetime(1, 1, 1, int(hours), int(minutes)))
    except ValueError as error:
        print('Error in --time parameter:\n', error)


def _get_value_from_date_parameter(date):
    # Separate each part of date that user has put as argument
    # Argument could f.ex. look like this: 2017/02/20
    year, month, day = re.findall(r"[\d]+", date)
    try:
        return datetime.date(datetime(int(year), int(month), int(day)))
    except ValueError as error:
        print('Error in --date parameter:\n', error)


def add(args):
    stamp = stamp_in(args)
    return stamp


def end(args):
    stamp_out(args)
    return


def tag(args):
    if args.id == 'current':
        stamp = current_stamp()
    else:
        stamp = query_for_workdays(workday_id=int(args.id))

    stamp = tag_stamp(args.date, args.time, stamp, args.tag)
    return


def status(args):
    try:
        workdays = query_for_workdays(args=args)
    except NoMatchingDatabaseEntryError as _err_msg:
        print(_err_msg)
        sys.exit(0)
    print_status(workdays)
    print_current_stamp()
    return


def export(args):
    export_filter = parse_export_filter(args.month, args.year, args.customer,
                                        args.project)
    try:
        workdays = query_db_export_filter('Workday', export_filter)
    except NoMatchingDatabaseEntryError as _err_msg:
        print(_err_msg)
        sys.exit(0)

    print_status(workdays)
    invoice = yes_or_no('Do you wish to create a Invoice containing these workdays?',
                        no_message='Canceled...',
                        no_function=sys.exit,
                        no_function_args=(0,),
                        yes_message='Creating new invoice!',
                        yes_function=create_invoice,
                        yes_function_args=(workdays,),
                        yes_function_kwargs={'export_to_pdf': True})
    return invoice


def delete(args):
    if args.id == 'current':
        args.id = current_stamp().id
    else:
        args.id = int(args.id)
    delete_workday_or_tag(args.id, args.tag)
    return


# Edit only supports customer for now
def edit(args):
    args.edit = edit_regex_resolver(args.edit)
    if args.id == 'current':
        args.id = current_stamp().id
    else:
        args.id = int(args.id)
    edit_workday(args)

    return


def version(*args, **kwargs):
    print(__version__)
    return


def main():
    # [Main parser]
    main_parser = argparse.ArgumentParser(description='''Register work hours.
                                          Hours get automatically sorted by date, and
                                          month is the default separator.''',
                                          epilog='''By arivarton
                                          (http://www.arivarton.com)''')
    main_parser.add_argument('-v', '--version', action='version', version=__version__,
                             help='Display current version.')

    # [Parent paramaters]

    # Date parameters
    date_parameters = argparse.ArgumentParser(add_help=False)
    date_parameters.add_argument('-D', '--date', type=lambda date: datetime.strptime(date, '%Y-%m-%d').date(), default=datetime.now().date(),
                                 help='Set date manually. Format is \'YYYY-mm-dd\'. Default is now.')
    date_parameters.add_argument('-T', '--time', type=lambda time: datetime.strptime(time, '%H:%M').time(), default=datetime.now().time(),
                                 help='Set time manually. Format is \'HH:MM\'. Default is now.')

    # Filter parameters
    filter_parameters = argparse.ArgumentParser(add_help=False)
    filter_parameters.add_argument('-f', '--filter', action='store_true',
                                   help='''Filter the output of status or pdf export. Use
                                   in combination with other arguments, f.ex status and customer:
                                   "status -f -c MyCompany"''')

    # Company parameters
    customer_parameters = argparse.ArgumentParser(add_help=False)
    customer_parameters.add_argument('-c', '--customer', type=str, default=STANDARD_CUSTOMER,
                                     help='Set customer to bill hours to.')

    # Project parameters
    project_parameters = argparse.ArgumentParser(add_help=False)
    project_parameters.add_argument('-p', '--project', type=str, default=STANDARD_PROJECT,
                                    help='Set the project to add hours to.')

    # Database parameters
    db_parameters = argparse.ArgumentParser(add_help=False)
    db_parameters.add_argument('-d', '--db', type=lambda db_name: os.path.join(DATA_DIR, db_name) + '.db',
                               default=os.path.join(DATA_DIR, DB_FILE),
                               help='Choose database name.')

    # [Subparsers]
    subparsers = main_parser.add_subparsers()

    # Add parser
    add_parser = subparsers.add_parser('add', help='''Add hours. If added with
                                       two separate times and/or dates the stamp
                                       will automatically finish.''',
                                       parents=[date_parameters,
                                                customer_parameters,
                                                project_parameters,
                                                db_parameters])
    add_parser.set_defaults(func=add)

    # End parser
    end_parser = subparsers.add_parser('end', help='End current stamp.',
                                       parents=[date_parameters,
                                                db_parameters])
    end_parser.set_defaults(func=end)

    # Tag parser
    tag_parser = subparsers.add_parser('tag', help='Tag a stamp.',
                                       parents=[date_parameters,
                                                db_parameters])
    tag_parser.add_argument('tag', type=str)
    tag_parser.add_argument('--id', type=str, default='current', help='''Choose
                               id to tag. Default is to tag current stamp.''')
    tag_parser.set_defaults(func=tag)

    # Status parser
    status_parser = subparsers.add_parser('status', help='Show registered hours.',
                                          parents=[filter_parameters,
                                                   customer_parameters,
                                                   project_parameters,
                                                   db_parameters])
    status_parser.add_argument('-s', '--status', action='store_true',
                               help='Print current state of stamp.')
    status_parser.add_argument('-a', '--all', action='store_true',
                               help='Show status of all registered days.')
    status_parser.set_defaults(func=status)

    # Export parser
    export_parser = subparsers.add_parser('export', help='Export hours to file.',
                                          parents=[filter_parameters,
                                                   db_parameters])
    export_parser.add_argument('month', type=str)
    export_parser.add_argument('year', type=str)
    export_parser.add_argument('customer', type=str, nargs='?')
    export_parser.add_argument('project', type=str, nargs='?')
    export_parser.set_defaults(func=export)

    # Delete parser
    delete_parser = subparsers.add_parser('delete',
                                          help='Delete a registered worktime.',
                                          parents=[db_parameters])
    delete_parser.add_argument('--id', type=str, default='current', help='''Choose
                               id to delete (or to delete tag under).
                               Default is to delete current stamp.''')
    delete_parser.add_argument('-t', '--tag', type=int, help='''Choose tag id to
                               delete''')
    delete_parser.set_defaults(func=delete)

    # Edit parser
    edit_parser = subparsers.add_parser('edit', help='''Edit everything related to
                                        workdays or tags.''',
                                        parents=[db_parameters])
    edit_parser.add_argument('--id', type=str, default='current', help='''Workday
                             id to edit (or to edit the tags for). Default is
                             to edit current stamp.''')
    edit_parser.add_argument('-t', '--tag', type=int, help='Choose tag to edit.')
    edit_parser.add_argument('edit', type=str, help='''
                             Add edit message in this format:
                             "date=2018-02-18,comment='Changing this'".
                             Valid arguments: date, time, comment, customer.
                             ''')
    edit_parser.set_defaults(func=edit)

    args = main_parser.parse_args()
    if vars(args):
        args.func(args)
    else:
        main_parser.print_help()


if __name__ == '__main__':
    main()
