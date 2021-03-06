import sys
from .add import new_stamp
from .end import end_stamp
from .edit import edit_workday, edit_customer, edit_project, edit_invoice
from .status import Status
from .delete import delete_workday_or_tag
from .tag import tag_stamp
from .export import export_invoice
from .exceptions import (NoMatchingDatabaseEntryError, CurrentStampNotFoundError,
                         NoMatchesError, TooManyMatchesError, CanceledByUser,
                         NonExistingId, DeleteNotAllowedError, TooManyMatchingDatabaseEntriesError)
from .helpers import error_handler
from .decorators import db_commit_decorator, no_db_no_action_decorator

__all__ = ['stamp_in',
           'stamp_out',
           'tag',
           'status',
           'export',
           'delete',
           'edit']

@db_commit_decorator
def stamp_in(args):
    try:
        new_stamp(args.db, args.customer, args.project, args.date,
                  args.time)
    except (CurrentStampNotFoundError, CanceledByUser) as err_msg:
        error_handler(err_msg, db=args.db)


@no_db_no_action_decorator
@db_commit_decorator
def stamp_out(args):
    try:
        end_stamp(args.db, args.date, args.time)
    except (CurrentStampNotFoundError, CanceledByUser) as err_msg:
        error_handler(err_msg, db=args.db)


@no_db_no_action_decorator
@db_commit_decorator
def tag(args):
    try:
        try:
            if args.id:
                stamp = args.db.get('Workday', id)
            else:
                stamp = args.db.current_stamp()
        except CurrentStampNotFoundError as err_msg:
            error_handler(err_msg, db=args.db)
        tag_stamp(args.db, args.date, args.time, stamp, args.tag)
    except CanceledByUser as err_msg:
        error_handler(err_msg, db=args.db)


@no_db_no_action_decorator
def status(args):
    called_from = args.parser_object.split(' ')[-1]
    args.interface = 'cli'
    try:
        if called_from != 'status':
            db_query = args.db.get(called_from[:-1].capitalize(), args.id)
            status_object = Status(db_query, args.config.values)
            if args.interface == 'cli':
                print(status_object)
            elif args.interface == 'ui':
                status_object.ui()
        else:
            try:
                status_object.print_current_stamp(args.db.current_stamp())
            except CurrentStampNotFoundError as err_msg:
                error_handler(err_msg)
    except NoMatchingDatabaseEntryError as err_msg:
        error_handler(err_msg, exit_on_error=False)
    except (CanceledByUser, NonExistingId) as err_msg:
        error_handler(err_msg, db=args.db)


@no_db_no_action_decorator
@db_commit_decorator
def export(args):
    try:
        export_invoice(args.db, args.year, args.month, args.customer,
                       args.project, args.config.values, args.pdf)
    except (NoMatchingDatabaseEntryError, TooManyMatchesError, NoMatchesError,
            CanceledByUser) as err_msg:
        error_handler(err_msg, db=args.db)


@no_db_no_action_decorator
@db_commit_decorator
def delete(args):
    try:
        if not args.id:
                args.id = args.db.current_stamp().id
        delete_workday_or_tag(args.db, args.id, args.tag)
    except (CurrentStampNotFoundError, NoMatchingDatabaseEntryError,
            DeleteNotAllowedError) as err_msg:
        error_handler(err_msg, db=args.db)


# Edit only supports customer for now
@no_db_no_action_decorator
@db_commit_decorator
def edit(args):
    edit_selection = args.parser_object.split(' ')[-1]
    try:
        if edit_selection == 'workday':
            if not args.id:
                try:
                    args.id = args.db.current_stamp().id
                except CurrentStampNotFoundError as err_msg:
                    error_handler(err_msg, db=args.db)
            changed_object = edit_workday(args)

        elif edit_selection == 'customer':
            changed_object = edit_customer(args)

        elif edit_selection == 'project':
            changed_object = edit_project(args.db, args.id, args.name, args.link)

        elif edit_selection == 'invoice':
            changed_object = edit_invoice(args.db, args.id, args.paid, args.sent)

    except (NoMatchingDatabaseEntryError, TooManyMatchingDatabaseEntriesError) as err_msg:
        error_handler(err_msg, db=args.db)

    args.db.add(changed_object)

def config(args):
    config_selection = args.parser_object.split(' ')[-1]
    if config_selection == 'show':
        print(args.config.values)
    elif config_selection == 'edit':
        for key, value in args.config.values.__dict__.items():
            if key in args.__dict__.keys():
                value = getattr(args, key)
                if value:
                    edit_value = getattr(args.config.values, key)
                    edit_value.value = value
        written_dict = {key: value.value for key, value in args.config.values.__dict__.items()} 
        args.config.write(written_dict)
    elif config_selection == 'provision':
        args.config.write({key: value.value for key, value in args.config.values.__dict__.items()})
