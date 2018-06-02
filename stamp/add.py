import sys
from datetime import datetime

from .mappings import Workday, Project, Customer
from .db import current_stamp, db_entry_exists
from .pprint import yes_or_no
from . import DB_SESSION


def _create_stamp(args, stamp):
    stamp.start = datetime.combine(args.date, args.time)
    DB_SESSION.add(stamp)
    DB_SESSION.commit()

    return stamp


def _add_details(Table):
    for key, column_info in Table.__mapper__.columns.items():
        if not key.endswith('id'):
            if not getattr(Table, key):
                user_value = input('Value for ' + column_info.name.lower() + ': ')
                setattr(Table, key, user_value)
    DB_SESSION.add(Table)
    DB_SESSION.commit()


def _create_project(project_name, customer_id):
    project = Project(name=project_name, customer_id=customer_id)
    yes_or_no('Do you wish to add project details?',
              no_message='Skipping project details!',
              yes_message='Adding project details. When entering a empty string the value will be set to None.',
              yes_function=_add_details,
              yes_function_args=(project,))
    DB_SESSION.add(project)
    DB_SESSION.commit()

    return project


def _create_customer(company_name):
    customer = Customer(name=company_name)
    yes_or_no('Do you wish to add customer details?',
              no_message='Skipping customer details!',
              yes_message='Adding customer details. When entering a empty string the value will be set to None.',
              yes_function=_add_details,
              yes_function_args=(customer,))
    DB_SESSION.add(customer)
    DB_SESSION.commit()

    return customer


def stamp_in(args):
    stamp = current_stamp()
    if stamp:
        stamp = yes_or_no('Already stamped in, do you wish to recreate the stamp with current date and time?',
                          no_message='Former stamp preserved!',
                          yes_message='Overwriting current stamp!',
                          yes_function=_create_stamp,
                          yes_function_args=(args, stamp))
    else:
        customer_id = db_entry_exists(Customer, 'name', args.company)
        project_id = db_entry_exists(Project, 'name', args.project)

        if customer_id:
            _workday = Workday(customer_id=customer_id)
        else:
            print('Customer', args.company, 'does not exist in DB!')
            __ = yes_or_no('Do you wish to create an entry for this customer?',
                           no_message='Canceling...',
                           no_function=sys.exit,
                           no_function_args=(0,),
                           yes_message='Creating database entry!',
                           yes_function=_create_customer,
                           yes_function_args=(args.company,))
            customer_id = __.id
            _workday = Workday(customer_id=customer_id)

        if project_id:
            _workday.project_id = project_id
        else:
            print('Project', args.project, 'does not exist in DB!')
            __ = yes_or_no('Do you wish to create an entry for this project?', # NOQA
                           no_message='Canceling...',
                           no_function=sys.exit,
                           no_function_args=(0,),
                           yes_message='Creating database entry!',
                           yes_function=_create_project,
                           yes_function_args=(args.project, customer_id))
            project_id = __.id
            _workday.project_id = project_id

        stamp = _create_stamp(args, _workday)

    print('Stamped in at %s - %s' % (stamp.start.date().isoformat(),
                                     stamp.start.time().isoformat()))

    return stamp
