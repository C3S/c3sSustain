import cryptacular.bcrypt
import datetime
import random
from sqlalchemy import (
    Table,
    ForeignKey,
    Column,
    Index,
    Integer,
    Text,
    Boolean,
    Unicode,
    Date,
    DateTime,
)
from sqlalchemy.orm import (
    relationship,
    synonym,
)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
import string
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


def make_random_string():
    """
    used as reference code
    """
    randomstring = u''.join(
        random.choice(
            string.ascii_uppercase + string.digits
        ) for x in range(5))
    # check if code is already used
    #print(
    #    "checking code: %s" % Abo.check_for_existing_refcode(
    #        randomstring))
    while (Abo.check_for_existing_refcode(randomstring)):
            # create a new one, if the new one already exists in the database
            #print("generating new code")
            randomstring = make_random_string()  # pragma: no cover
    the_string = u'' + randomstring + u'SustainC3S'
    #print "return that string: {}".format(the_string)
    return the_string

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()
crypt = cryptacular.bcrypt.BCRYPTPasswordManager()


def hash_password(password):
    return unicode(crypt.encode(password))


class Group(Base):
    """
    groups aka roles for users
    """
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(30), unique=True, nullable=False)

    def __str__(self):
        return 'group:%s' % self.name

    def __init__(self, name):
        self.name = name

    # @classmethod
    # def get_staff_group(cls, groupname=u'staff'):
    #     dbsession = DBSession()
    #     staff_group = dbsession.query(
    #         cls).filter(cls.name == groupname).first()
    #     #print('=== get_staffers_group:' + str(staff_group))
    #     return staff_group

# table for relation between staffers and groups
staff_groups = Table(
    'staff_groups', Base.metadata,
    Column(
        'staff_id', Integer, ForeignKey('staff.id'),
        primary_key=True, nullable=False),
    Column(
        'group_id', Integer, ForeignKey('groups.id'),
        primary_key=True, nullable=False)
)


class Staff(Base):
    """
    C3S staff may login and do things
    """
    __tablename__ = 'staff'
    id = Column(Integer, primary_key=True)
    login = Column(Unicode(255), unique=True)
    _password = Column('password', Unicode(60))
    last_password_change = Column(
        DateTime,
        default=func.current_timestamp())
    email = Column(Unicode(255))
    groups = relationship(
        Group,
        secondary=staff_groups,
        backref="staff")

    def _init_(self, login, password, email):  # pragma: no cover
        self.login = login
        self.password = password
        self.last_password_change = datetime.now()
        self.email = email

    #@property
    #def __acl__(self):
    #    return [
    #        (Allow,                           # user may edit herself
    #         self.username, 'editUser'),
    #        #'user:%s' % self.username, 'editUser'),
    #        (Allow,                           # accountant group may edit
    #         'group:accountants', ('view', 'editUser')),
    #        (Allow,                           # admin group may edit
    #         'group:admins', ('view', 'editUser')),
    #    ]

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = hash_password(password)

    password = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password)

    @classmethod
    def get_by_id(cls, id):
        return DBSession.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_by_login(cls, login):
        #dbSession = DBSession()
        return DBSession.query(cls).filter(cls.login == login).first()

    @classmethod
    def check_password(cls, login, password):
        #dbSession = DBSession()
        staffer = cls.get_by_login(login)
        #if staffer is None:  # ?
        #    return False
        #if not staffer:  # ?
        #    return False
        return crypt.check(staffer.password, password)

    # this one is used by RequestWithUserAttribute
    @classmethod
    def check_user_or_None(cls, login):
        """
        check whether a user by that username exists in the database.
        if yes, return that object, else None.
        returns None if username doesn't exist
        """
        login = cls.get_by_login(login)  # is None if user not exists
        return login

    @classmethod
    def delete_by_id(cls, id):
        _del = DBSession.query(cls).filter(cls.id == id).first()
        _del.groups = []
        DBSession.query(cls).filter(cls.id == id).delete()
        return

    @classmethod
    def get_all(cls):
        return DBSession.query(cls).all()


def sponsorshipGrade(amount):
    '''
    get sponsorship_grade for a particular amount
    '''
    #if int(amount) >= 250:  # 250 ..
    #    print "more than 250"
    #    return '7'
    #el
    if int(amount) >= 100:  # 100 - 249
        #print "more than 100"
        return '6'
    elif int(amount) >= 50:  # 50 - 99
        #print "more than 50"
        return '5'
    elif int(amount) >= 30:  # 30 - 49
        #print "more than 30"
        return '4'
    elif int(amount) >= 15:  # 15 - 29
        #print "more than 15"
        return '3'
    elif int(amount) >= 6:  # 6 - 14
        #print "more than 6"
        return '2'
    elif int(amount) == 5:  # 5
        #print "exactely 5"
        return '1'
    else:
        return '0'


class Abo(Base):
    '''
    when supporters use the form, their submissions are saved here
    '''
    __tablename__ = 'abos'
    __table_args__ = ({'sqlite_autoincrement': True})
    id = Column(Integer, primary_key=True)
    # form data
    name = Column(Unicode)
    email = Column(Unicode)
    amount = Column(Integer)
    locale = Column(Unicode)
    date_issued = Column(Date)  # started when?
    # computed info
    email_is_confirmed = Column(Boolean, default=False)  # once 1st paym. rec'd
    refcode = Column(Text)  # verwendungszweck / sent with first email
    # payment info
    payment_received = Column(Boolean, default=False)  # got dack?
    payment_received_date = Column(Date)  # when first
    linkcode = Column(Text)  # part of link to sonsors page and image
    payment_last_date = Column(Date)  # when latest
    payment_due_date = Column(Date)  # when to expect next payment
    # we send email to users with links to their pgn and html-page
    payment_confirmed_email = Column(Boolean, default=False)  # sent mail
    payment_confirmed_email_date = Column(Date)  # when
    # if no money comes in ... we send reminders
    payment_overdue = Column(Boolean, default=False)  # should pay soon
    payment_reminder_sent = Column(Boolean, default=False)  # should pay soon
    payment_reminder_sent_date = Column(Date)  # when to expect next payment

    def __init__(self,
                 name, email, amount):
        self.name = name
        self.email = email
        self.amount = amount
        self.date_issued = datetime.datetime.now()
        self.refcode = make_random_string()
        #print("DEBUG========= {}".format(self.refcode))

    def get_sponsorshipGrade(self):
        '''
        get sponsorship_grade for a particular abo
        '''
        #if int(self.amount) >= 250:  # 250 ..
        #    print "more than 250"
        #    return '7'
        #el
        if int(self.amount) >= 100:  # 100 - 249
            print "more than 100"
            return '6'
        elif int(self.amount) >= 50:  # 50 - 99
            print "more than 50"
            return '5'
        elif int(self.amount) >= 30:  # 30 - 49
            print "more than 30"
            return '4'
        elif int(self.amount) >= 15:  # 15 - 29
            print "more than 15"
            return '3'
        elif int(self.amount) >= 6:  # 6 - 14
            print "more than 6"
            return '2'
        elif int(self.amount) == 5:  # 5
            print "exactely 5"
            return '1'
        else:
            return '0'

    @classmethod
    def check_for_existing_refcode(cls, code):
        '''
        check if refcode exists in DB
        '''
        return DBSession.query(cls).filter(
            cls.refcode == code).first() is not None

    @classmethod
    def check_for_existing_linkcode(cls, code):
        '''
        check if linkcode exists in DB
        '''
        return DBSession.query(cls).filter(
            cls.refcode == code).first() is not None

    @classmethod
    def get_by_id(cls, _id):
        '''
        get subscription by id
        '''
        return DBSession.query(cls).filter(
            cls.id == _id).first()

    @classmethod
    def delete_by_id(cls, _id):
        '''
        delete subscription by id
        '''
        DBSession.query(cls).filter(
            cls.id == _id).delete()
        return

    @classmethod
    def get_by_code(cls, code):
        '''
        get subscription by refcode
        '''
        return DBSession.query(cls).filter(
            cls.refcode == code).first()

    @classmethod
    def get_by_linkcode(cls, linkcode):
        '''
        get subscription by refcode
        '''
        return DBSession.query(cls).filter(
            cls.linkcode == linkcode).first()

    @classmethod
    def get_number(cls):
        '''
        get number of objects in DB
        '''
        return DBSession.query(cls).count()

    @classmethod
    def get_matching_refcodes(cls, prefix):
        '''
        return only reference codes matching the prefix
        '''
        all = DBSession.query(cls).all()
        refcodes = []
        for item in all:
            if item.refcode.startswith(prefix):
                refcodes.append(item.refcode)
        print("number of items found: %s" % len(refcodes))
        return refcodes

    @classmethod
    def abo_listing(cls, order_by, how_many=10, offset=0, order='asc'):
        '''
        get all objects in DB
        '''
        try:
            attr = getattr(cls, order_by)
            order_function = getattr(attr, order)
        except:
            raise Exception("Invalid order_by ({0}) or order value "
                            "({1})".format(order_by, order))
        _how_many = int(offset) + int(how_many)
        _offset = int(offset)
        return DBSession.query(
            cls).order_by(order_function()).slice(_offset, _how_many).all()

    @classmethod
    def get_sum_abos_total(cls):
        abos = DBSession.query(cls).all()
        sum_total = 0
        for abo in abos:
            sum_total += int(abo.amount)
        return sum_total

    @classmethod
    def get_sum_abos_unpaid(cls):
        abos = DBSession.query(cls).all()
        sum_total = 0
        for abo in abos:
            if not abo.payment_received:
                sum_total += int(abo.amount)
        return sum_total

    @classmethod
    def get_sum_abos_paid(cls):
        abos = DBSession.query(cls).all()
        sum_total = 0
        for abo in abos:
            if abo.payment_received:
                sum_total += int(abo.amount)
        return sum_total

Index('abo_index', Abo.name, mysql_length=255)


class Transfers(Base):
    '''
    the transfers received are saved here
    '''
    __tablename__ = 'transfers'
    __table_args__ = ({'sqlite_autoincrement': True})
    id = Column(Integer, primary_key=True)
    abo_id = Column(Unicode)  # whose money?
    date = Column(DateTime)  # received when?
    amount = Column(Integer)  # how much?

    def __init__(self, abo_id, date, amount):
        self.abo_id = abo_id
        self.date = date
        self.amount = amount

    @classmethod
    def get_sum_transfers_by_aboid(cls, abo_id):
        transfers = DBSession.query(
            cls).filter(cls.abi_id == abo_id).all()
        sum = 0
        for transfer in transfers:
            sum += transfer.amount
        return sum

    @classmethod
    def get_all_transfers_by_aboid(cls, abo_id):
        return DBSession.query(
            cls).filter(cls.abo_id == abo_id).all()
