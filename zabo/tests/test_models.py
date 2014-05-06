# -*- coding: utf-8  -*-
#import os
import unittest
import transaction
#from pyramid.config import Configurator
from pyramid import testing
#from datetime import date
from sqlalchemy import create_engine
#from sqlalchemy.exc import IntegrityError
from zabo.models import (
    DBSession,
    Base,
    Group,
    Staff,
    Abo,
)
DEBUG = False


#class ModelTest(unittest.TestCase):
#    def test_make_random_string(self):
#        from zabo.models import make_random_string

class ZaboModelTestBase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
            #print("removing old DBSession ===================================")
        except:
            #print("no DBSession to remove ===================================")
            pass
        #engine = create_engine('sqlite:///test_models.db')
        engine = create_engine('sqlite:///:memory:')
        self.session = DBSession
        DBSession.configure(bind=engine)  # XXX does influence self.session!?!
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        self.session.remove()
        #os.remove('test_models.db')

    def _getTargetClass(self):
        return Abo

    def _makeOne(self,
                 name=u'SomeNäme',
                 email=u'some1@shri.de',
                 amount=u'23',
                 ):
        #print "type(self.session): " + str(type(self.session))
        return self._getTargetClass()(  # order of params DOES matter
            name, email, amount
        )

    def _makeAnotherOne(self,
                        name=u'SomeOther',
                        email=u'some2@shri.de',
                        amount=u'42',
                        ):
        return self._getTargetClass()(  # order of params DOES matter
            name, email, amount
        )

    def _getGroupClass(self):
        return Group

    def _make_group(self,
                   name=u'my_group'):
        return self._getGroupClass()(
            name,
        )

    def _getStaffClass(self):
        return Staff


class GroupModelTests(ZaboModelTestBase):
    def setUp(self):
        super(GroupModelTests, self).setUp()
        #with transaction.manager:
        #    group1 = Group(name=u"Group1")
        #    DBSession.add(group1)
        #    DBSession.flush()

    def test_constructor(self):
        instance = self._make_group()
        print(instance.name)
        self.assertEqual(instance.name, u'my_group', "No match!")


class ZaboModelTests(ZaboModelTestBase):

    def setUp(self):
        super(ZaboModelTests, self).setUp()
        with transaction.manager:
            abo1 = Abo(  # german
                name=u'SomeFirstnäme',
                email=u'some@shri.de',
                amount=u"12345",
            )
            DBSession.add(abo1)
            DBSession.flush()

    def test_constructor(self):
        instance = self._makeOne()

        self.assertEqual(instance.name, u'SomeNäme', "No match!")
        self.assertEqual(instance.email, u'some1@shri.de', "No match!")
        self.assertEqual(instance.amount, u'23', "No match!")

    # def test_get_by_code(self):
    #     instance = self._makeOne()
    #     #session = DBSession()
    #     self.session.add(instance)
    #     myClass = self._getTargetClass()
    #     instance_from_DB = myClass.get_by_code(u'ABCDEFGHIK')
    #     #self.session.commit()
    #     #self.session.remove()
    #     #print instance_from_DB.email
    #     if DEBUG:
    #         print "myClass: " + str(myClass)
    #         #        print "str(myUserClass.get_by_username('SomeUsername')): "
    #         # + str(myUserClass.get_by_username('SomeUsername'))
    #         #        foo = myUserClass.get_by_username(instance.username)
    #         #        print "test_get_by_username: type(foo): " + str(type(foo))
    #     self.assertEqual(instance.name, u'SomeNäme')
    #     self.assertEqual(instance.email, u'some1@shri.de')

    def test_get_by_id(self):
        instance = self._makeOne()
        #session = DBSession()
        self.session.add(instance)
        self.session.flush()
        _id = instance.id
        _date_issued = instance.date_issued
        myClass = self._getTargetClass()
        instance_from_DB = myClass.get_by_id(_id)
        #self.session.commit()
        #self.session.remove()
        #print instance_from_DB.email
        if DEBUG:
            print "myClass: " + str(myClass)
            #        print "str(myUserClass.get_by_username('SomeUsername')): "
            # + str(myUserClass.get_by_username('SomeUsername'))
            #        foo = myUserClass.get_by_username(instance.username)
            #        print "test_get_by_username: type(foo): " + str(type(foo))
        self.assertEqual(instance_from_DB.name, u'SomeNäme')
        self.assertEqual(instance_from_DB.email, u'some1@shri.de')
        self.assertEqual(instance_from_DB.amount, u'23')

    def test_delete_by_id(self):
        instance = self._makeOne()
        #session = DBSession()
        self.session.add(instance)
        myClass = self._getTargetClass()
        instance_from_DB = myClass.get_by_id('1')
        myClass.delete_by_id('1')
        #print del_instance_from_DB
        instance_from_DB = myClass.get_by_id('1')
        self.assertEqual(None, instance_from_DB)

    # def test_check_user_or_None(self):
    #     instance = self._makeOne()
    #     #session = DBSession()
    #     self.session.add(instance)
    #     myMembershipSigneeClass = self._getTargetClass()
    #     # get first dataset (id = 1)
    #     result1 = myMembershipSigneeClass.check_user_or_None('1')
    #     #print check_user_or_None
    #     self.assertEqual(1, result1.id)
    #     # get invalid dataset
    #     result2 = myMembershipSigneeClass.check_user_or_None('1234567')
    #     #print check_user_or_None
    #     self.assertEqual(None, result2)

    # def test_check_for_existing_confirm_code(self):
    #     instance = self._makeOne()
    #     self.session.add(instance)
    #     myClass = self._getTargetClass()

    #     result1 = myClass.check_for_existing_confirm_code(
    #         u'ABCDEFGHIK')
    #     #print result1  # True
    #     self.assertEqual(result1, True)
    #     result2 = myClass.check_for_existing_confirm_code(
    #         u'ABCDEFGHIK0000000000')
    #     #print result2  # False
    #     self.assertEqual(result2, False)

    def test_abo_listing(self):
        instance = self._makeOne()
        self.session.add(instance)
        instance2 = self._makeAnotherOne()
        self.session.add(instance2)
        myClass = self._getTargetClass()

        result1 = myClass.abo_listing("id")
        self.failUnless(result1[0].name == u"SomeFirstnäme")
        self.failUnless(result1[1].name == u"SomeNäme")

    # def test_member_listing_exception(self):
    #     instance = self._makeOne()
    #     self.session.add(instance)
    #     instance2 = self._makeAnotherOne()
    #     self.session.add(instance2)
    #     myMembershipSigneeClass = self._getTargetClass()

    #     #self.assertRaises(myMembershipSigneeClass, member_listing, "foo")
    #     with self.assertRaises(Exception):
    #         result1 = myMembershipSigneeClass.member_listing("foo")
    #     #self.failUnless(result1[0].firstname == u"SomeFirstnäme")
    #     #self.failUnless(result1[1].firstname == u"SomeFirstnäme")
    #     #self.failUnless(result1[2].firstname == u"SomeFirstname")


class TestSponsorshipGrade(ZaboModelTestBase):
    def setUp(self):
        super(TestSponsorshipGrade, self).setUp()
        instance = self._makeOne(name=u"XXX", email=u'0@shri.de',
                                 amount=3)
        self.session.add(instance)
        instance = self._makeOne(name=u"ABC", email=u'1@shri.de',
                                 amount=5)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"GHI", email=u'2@shri.de',
                                        amount=12)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"JKL", email=u'3@shri.de',
                                        amount=17)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"MNO", email=u'4@shri.de',
                                        amount=42)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"PQR", email=u'5@shri.de',
                                        amount=55)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"STU", email=u'6@shri.de',
                                        amount=112)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"VWX", email=u'7@shri.de',
                                        amount=370)
        self.session.add(instance)
        self.session.flush()

    def test_get_sponsorshipGrade(self):
        for i in range(1, 9):
            abo = Abo.get_by_id(i)
            res = abo.get_sponsorshipGrade()
            #print "{}: amount: {} grade: {}".format(i, abo.amount, res)
            self.assertEqual(int(res), i-1)


class TestAboListing(ZaboModelTestBase):
    def setUp(self):
        super(TestAboListing, self).setUp()
        instance = self._makeOne(name=u"ABC", email=u'1@shri.de',
                                 amount=5)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"DEF", email=u'2@shri.de',
                                        amount=12)
        self.session.add(instance)
        instance = self._makeAnotherOne(name=u"GHI", email=u'3@shri.de',
                                        amount=123)
        self.session.add(instance)
        self.session.flush()
        self.class_under_test = self._getTargetClass()

    def test_orderByName_sortedByLastname(self):
        #print "now test " * 45
        result = self.class_under_test.abo_listing(order_by='name')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("ABC", result[0].name)
        self.assertEqual("GHI", result[-1].name)

    def test_orderByNameOrderAsc_sortedByLastname(self):
        result = self.class_under_test.abo_listing(
            order_by='name', order="asc")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("ABC", result[0].name)
        self.assertEqual("GHI", result[-1].name)

    def test_orderByNameOrderDesc_sortedByLastname(self):
        result = self.class_under_test.abo_listing(
            order_by='name', order="desc")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("GHI", result[0].name)
        self.assertEqual("ABC", result[-1].name)

    def test_orderByInvalidName_raisesException(self):
        self.assertRaises(self.class_under_test.abo_listing,
                          order_by='unknown', order="desc")
        self.assertRaises(self.class_under_test.abo_listing,
                          order_by=None, order="desc")
        self.assertRaises(self.class_under_test.abo_listing,
                          order_by="", order="desc")

    def test_orderInvalid_raisesException(self):
        self.assertRaises(self.class_under_test.abo_listing,
                          order_by='name', order="unknown")
        self.assertRaises(self.class_under_test.abo_listing,
                          order_by='name', order="")
        self.assertRaises(self.class_under_test.abo_listing,
                          order_by='name', order=None)


class StaffModelTests(ZaboModelTestBase):

    def setUp(self):
        super(StaffModelTests, self).setUp()
        with transaction.manager:
            staff1 = Staff(  # german
                login=u'SomeFoonäme',
                email=u'someFoo@shri.de',
                password=u"12345",
            )
            DBSession.add(staff1)
            DBSession.flush()

    def test_constructor(self):
        staff1 = Staff.get_by_id(u'1')
        #print(instance.address1)
        print dir(staff1)
        self.assertEqual(staff1.login, u'SomeFoonäme', "No match!")
        self.assertEqual(staff1.email, u'someFoo@shri.de', "No match!")

    def test_get_by_login(self):
        staff1 = Staff.get_by_login(u'SomeFoonäme')
        myClass = self._getStaffClass()
        instance_from_DB = myClass.get_by_login(u'SomeFoonäme')

    def test_check_user_or_None(self):
        staff1 = Staff.get_by_login(u'SomeFoonäme')
        self.assertEqual(
            Staff.check_user_or_None(u'SomeFoonäme'),
            staff1)

    def test_delete_by_id(self):
        Staff.delete_by_id(1)
        self.assertEqual(
            Staff.check_user_or_None(u'SomeFoonäme'),
            None)

    def test_get_all(self):
        all_staff = Staff.get_all()
        self.assertEqual(
            len(all_staff),
            1)
