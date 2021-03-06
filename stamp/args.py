import argparse
import os

from . import __version__
from .args_helpers import *
from .main import stamp_in, stamp_out, tag, status, export, delete, edit, config
from .exceptions import RequiredValueError
from .config import Config
from .constants import DATA_DIR, DB_FILE, CONFIG_DIR, CONFIG_FILE

__all__ = ['parse']

settings = Config(None)

def parse(args):
    # [Main parser]
    main_parser = argparse.ArgumentParser(description='''Register work hours.
                                          Hours get automatically sorted by date, and
                                          month is the default separator.''',
                                          epilog='''By arivarton
                                          (http://www.arivarton.com)''')
    main_parser.add_argument('-v', '--version', action='version', version=__version__,
                             help='Display current version.')
    main_parser.add_argument('--db', action=DbAction)
    main_parser.add_argument('--config', action=ConfigAction)

    # [Parent paramaters]

    # Date parameters
    date_parameters = argparse.ArgumentParser(add_help=False)
    date_parameters.add_argument('-D', '--date', action=DateAction)
    date_parameters.add_argument('-T', '--time', action=TimeAction)

    # Filter parameters
    filter_parameters = argparse.ArgumentParser(add_help=False)
    filter_parameters.add_argument('--date_from')
    filter_parameters.add_argument('--date_to')
    filter_parameters.add_argument('--time_from')
    filter_parameters.add_argument('--time_to')

    # Company parameters
    customer_parameters = argparse.ArgumentParser(add_help=False)
    customer_parameters.add_argument('-c', '--customer', action=FromEnvAction,
                                    env_var='STAMP_STANDARD_CUSTOMER',
                                    help='Set customer to bill hours to.')

    # Project parameters
    project_parameters = argparse.ArgumentParser(add_help=False)
    project_parameters.add_argument('-p', '--project', action=FromEnvAction,
                                    env_var='STAMP_STANDARD_PROJECT',
                                    help='Set the project to add hours to.')

    # [Subparsers]
    main_subparsers = main_parser.add_subparsers()


    # Add parser
    in_parser = main_subparsers.add_parser('in', aliases=['i'],
                                           help='''Add stamp. If added with
                                           two separate times and/or dates the stamp
                                           will automatically finish.''',
                                      parents=[date_parameters,
                                               customer_parameters,
                                               project_parameters])
    in_parser.set_defaults(func=stamp_in)


    # End parser
    out_parser = main_subparsers.add_parser('out', aliases=['o'],
                                            help='End current stamp.',
                                            parents=[date_parameters])
    out_parser.set_defaults(func=stamp_out)


    # Tag parser
    tag_parser = main_subparsers.add_parser('tag', aliases=['t'],
                                            help='Tag a stamp.',
                                            parents=[date_parameters])
    tag_parser.add_argument('id', type=int, nargs='?')
    tag_parser.add_argument('tag', type=str)
    tag_parser.set_defaults(func=tag, parser_object=tag_parser.prog)


    # Status parser
    status_parser = main_subparsers.add_parser('status', aliases=['s'],
                                               help='Show registered hours.',
                                               parents=[filter_parameters,
                                                        customer_parameters,
                                                        project_parameters])
    status_parser.set_defaults(func=status, parser_object=status_parser.prog)

    status_subparsers = status_parser.add_subparsers()

    status_workdays_parser = status_subparsers.add_parser('workdays', aliases=['w'],
                                                          help='Show status of workdays.',
                                                          parents=[date_parameters])
    status_workdays_parser.add_argument('id', type=int, nargs='?')
    status_workdays_parser.set_defaults(func=status, parser_object=status_workdays_parser.prog)

    status_invoices_parser = status_subparsers.add_parser('invoices', aliases=['i'],
                                                          help='Show status of invoices.',
                                                          parents=[date_parameters])
    status_invoices_parser.add_argument('id', type=int, nargs='?')
    status_invoices_parser.set_defaults(func=status, parser_object=status_invoices_parser.prog)


    # Export parser
    export_parser = main_subparsers.add_parser('export', aliases=['x'],
                                               help='Export hours to file.',
                                               parents=[filter_parameters])
    export_parser.add_argument('month', type=str)
    export_parser.add_argument('year', type=int)
    export_parser.add_argument('customer', type=str)
    export_parser.add_argument('-p', '--pdf', action='store_true',
                               help='Export to PDF.')
    export_parser.add_argument('project', type=str, nargs='?')
    export_parser.set_defaults(func=export)


    # Delete parser
    delete_parser = main_subparsers.add_parser('delete', aliases=['d'],
                                               help='Delete a registered worktime. \
                                                    Be aware that running this without \
                                                    id will delete current stamp!')
    delete_parser.add_argument('id', type=int, nargs='?', default=None)
    delete_parser.add_argument('-t', '--tag', type=int, help='''Choose tag id to
                               delete.''')
    delete_parser.add_argument('-f', '--force', action='store_true',
                               help='Force deletion. Use with caution, this could\
                               corrupt the database.')
    delete_parser.set_defaults(func=delete)


    # Edit parser
    edit_parser = main_subparsers.add_parser('edit', aliases=['e'],
                                             help='Edit options.')
    edit_subparsers = edit_parser.add_subparsers()
    # Edit workday
    edit_workday_parser = edit_subparsers.add_parser('workday', aliases=['w', 'wd'],
                                                     help='Edit a selected workday.')
    edit_workday_parser.add_argument('id', type=int)
    edit_workday_parser.add_argument('-c', '--comment', type=str,
                                     help='Change comment.')
    edit_workday_parser.add_argument('-u', '--customer', type=str,
                                     help='Change customer.')
    edit_workday_parser.add_argument('-p', '--project', type=str,
                                     help='Change project.')
    edit_workday_parser.set_defaults(func=edit, parser_object=edit_workday_parser.prog)
    edit_workday_subparsers = edit_workday_parser.add_subparsers()
    # Edit workday time
    edit_workday_time_parser = edit_workday_subparsers.add_parser('time', aliases=['t'],
                                                                  help='Edit the time registered on a workday.')
    edit_workday_time_parser.add_argument('-s', '--start', type=str,
                                          help='''Specify start time to store.''')
    edit_workday_time_parser.add_argument('-e', '--end', type=str,
                                          help='''Specify start time to store.''')
    # Edit workday tag
    edit_workday_tag_parser = edit_workday_subparsers.add_parser('tag', aliases=['tg'],
                                                                 help='Edit tags related to selected workday.')
    # Edit customer
    edit_customer_parser = edit_subparsers.add_parser('customer', aliases=['c'],
                                                      help='Edit a selected customer.')
    edit_customer_parser.add_argument('id', type=int)
    edit_customer_parser.add_argument('-n', '--name', type=str,
                                      help='Change name.')
    edit_customer_parser.add_argument('-c', '--contact', type=str,
                                      help='Change contact person.')
    edit_customer_parser.add_argument('-o', '--org_nr', type=str,
                                      help='Change organization number.')
    edit_customer_parser.add_argument('-a', '--address', type=str,
                                      help='Change address.')
    edit_customer_parser.add_argument('-z', '--zip_code', type=str,
                                      help='Change zip code.')
    edit_customer_parser.add_argument('-m', '--mail', type=str,
                                      help='Change mail.')
    edit_customer_parser.add_argument('-p', '--phone', type=str,
                                      help='Change phone number.')
    edit_customer_parser.set_defaults(func=edit, parser_object=edit_customer_parser.prog)

    # Edit project
    edit_project_parser = edit_subparsers.add_parser('project', aliases=['p'],
                                                     help='Edit a selected project.')
    edit_project_parser.add_argument('id', type=int)
    edit_project_parser.add_argument('-n', '--name', type=str,
                                     help='Change name.')
    edit_project_parser.add_argument('-u', '--link', type=str,
                                     help='Change link to website.')
    edit_project_parser.set_defaults(func=edit, parser_object=edit_project_parser.prog)

    # Edit invoice
    edit_invoice_parser = edit_subparsers.add_parser('invoice', aliases=['i'],
                                                     help='Edit a selected invoice.')
    edit_invoice_parser.add_argument('id', type=int)
    edit_invoice_parser.add_argument('-p', '--paid', action='store_true',
                                     help='Set or unset an invoices paid option.')
    edit_invoice_parser.add_argument('-s', '--sent', action='store_true',
                                     help='Set or unset an invoices sent option.')
    edit_invoice_parser.set_defaults(func=edit, parser_object=edit_invoice_parser.prog)


    # Config parser
    config_parser = main_subparsers.add_parser('config', aliases=['c'],
                                               help='See and edit config options.',
                                               description='Config file path is %s' % os.path.join(CONFIG_DIR, CONFIG_FILE))
    config_subparsers = config_parser.add_subparsers()
    # Show config
    config_show_parser = config_subparsers.add_parser('show', aliases=['s'],
                                                      help='Display current configuration values.')
    config_show_parser.set_defaults(func=config, parser_object=config_show_parser.prog)
    # Edit config
    config_edit_parser = config_subparsers.add_parser('edit', aliases=['e'],
                                                      help='Edit configuration values.')
    for key, value in settings.values.__dict__.items():
        if value.choices:
            config_edit_parser.add_argument('--%s' % key, type=str, choices=value.choices)
        else:
            config_edit_parser.add_argument('--%s' % key, type=str)
    config_edit_parser.set_defaults(func=config, parser_object=config_edit_parser.prog)
    # Provision config
    config_provision_parser = config_subparsers.add_parser('provision', aliases=['p'],
                                                           help='Provision a new config file with default values.')
    config_provision_parser.set_defaults(func=config, parser_object=config_provision_parser.prog)

    return main_parser.parse_args(args)
