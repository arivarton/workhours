from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, validates

from .helpers import get_month_names

__all__ = ['Customer',
           'Project',
           'Invoice',
           'Workday',
           'Tag']

Base = declarative_base()


class Customer(Base):
    __tablename__ = 'customer'

    id = Column(Integer, primary_key=True)
    name = Column('Customer name', String, unique=True)
    contact_person = Column('Contact person', String, default=None)
    org_nr = Column('Organisation number', String, default=None)
    address = Column('Address', String, default=None)
    zip_code = Column('ZIP Code', String, default=None)
    mail = Column('Invoice e-mail', String, default=None)
    phone = Column('Phone number', String, default=None)

    workdays = relationship('Workday', order_by='Workday.start',
                            cascade='all, delete, delete-orphan', lazy='dynamic',
                            backref='customer')
    projects = relationship('Project', order_by='Project.id',
                            cascade='all, delete, delete-orphan', lazy='dynamic')
    invoices = relationship('Invoice', order_by='Invoice.created', lazy='dynamic',
                            backref='customer')


class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column('Project name', String)
    link = Column('Project url', String, default=None)

    customer_id = Column(ForeignKey('customer.id'))

    workdays = relationship('Workday', order_by='Workday.start', lazy='dynamic',
                            backref='project')


class Invoice(Base):
    __tablename__ = 'invoice'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now())
    pdf = Column('PDF Directory', String, unique=True, default=None)
    month = Column(String, default=None)
    year = Column(String, default=None)
    paid = Column(Boolean, default=False)
    sent = Column(Boolean, default=False)

    customer_id = Column(ForeignKey('customer.id'))

    workdays = relationship('Workday', order_by='Workday.start',
                            backref='invoice')

    @validates('month')
    def validate_month(self, key, value): # NOQA
        assert value in get_month_names()
        return value


class Workday(Base):
    __tablename__ = 'workday'

    id = Column(Integer, primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime, default=None)

    customer_id = Column(ForeignKey('customer.id'))
    project_id = Column(ForeignKey('project.id'))
    invoice_id = Column(ForeignKey('invoice.id'), default=None)

    tags = relationship('Tag', order_by='Tag.recorded',
                        cascade='all, delete, delete-orphan', lazy='dynamic',
                        backref='workday')


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    recorded = Column(DateTime)
    tag = Column(String)

    workday_id = Column(ForeignKey('workday.id'))
