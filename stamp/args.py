import os
import argparse

from . import __version__
from .args_helpers import DateAction, TimeAction
from .main import add, end, tag, status, export, delete, edit

from .settings import STANDARD_CUSTOMER, STANDARD_PROJECT, DATA_DIR, DB_FILE


def parse(args):
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
    date_parameters.add_argument('-D', '--date', action=DateAction)
    date_parameters.add_argument('-T', '--time', action=TimeAction)

    # Filter parameters
    filter_parameters = argparse.ArgumentParser(add_help=False)
    filter_parameters.add_argument('-f', '--filter', action='store_true',
                                   help='''Filter the output of status or pdf export.
                                   Use this format:
                                   "date_from=2018-02-18,date_to=2018-04-20,
                                   company='somecompany'".''')

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
    in_parser = subparsers.add_parser('in', help='''Add stamp. If added with
                                       two separate times and/or dates the stamp
                                       will automatically finish.''',
                                      parents=[date_parameters,
                                               customer_parameters,
                                               project_parameters,
                                               db_parameters])
    in_parser.set_defaults(func=add)

    # End parser
    out_parser = subparsers.add_parser('out', help='End current stamp.',
                                       parents=[date_parameters,
                                                db_parameters])
    out_parser.set_defaults(func=end)

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
    status_parser.add_argument('--invoices',
                               action='store_true',
                               help='Show status of invoices.')
    status_parser.add_argument('-s', '--show_superseeded',
                               action='store_true',
                               help='Show all created invoices. Only valid with the invoices option.')
    status_parser.set_defaults(func=status)

    # Export parser
    export_parser = subparsers.add_parser('export', help='Export hours to file.',
                                          parents=[filter_parameters,
                                                   db_parameters])
    export_parser.add_argument('month', type=str)
    export_parser.add_argument('year', type=str)
    export_parser.add_argument('customer', type=str)
    export_parser.add_argument('-p', '--pdf', action='store_true',
                               help='Export to PDF.')
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

    return main_parser.parse_args(args)