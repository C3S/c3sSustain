import unittest
import transaction

from pyramid import testing

from zabo.models import (
    DBSession,
    Abo,
)


class TestBackendViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        #self.config.include('pyramid_mailer.debug')
        self.config.include('pyramid_mailer.testing')
        from sqlalchemy import create_engine
        engine = create_engine('sqlite://')
        from zabo.models import (
            Base,
        )
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            model = Abo(name=u'one', email=u'foo@shri.de', amount=55)
            DBSession.add(model)

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_send_mail_view(self):
        '''
        tests for the send_email_view view in backend_views.py
        i.e. to send out transfer information emails
        '''
        from zabo.backend_views import send_mail_view
        self.config.add_route('dash', '/dash')
        '''
        if the requested id does not exist, redirect to the dashboard
        '''
        request = testing.DummyRequest()
        request.registry.settings['the_url'] = 'http://foobar.com'
        request.registry.settings['mail_from'] = 'dev@c3s.cc'
        request.matchdict['abo_id'] = u'1foo'  # does not exist
        result = send_mail_view(request)
        #print result.location
        self.assertTrue('dash' in result.location)  # redirected
        '''
        if the id does exist, send email
        '''
        # first, create an abo in the DB and thus an id to match
        new_abo = Abo(
            name=u'foobar',
            email=u'foo@shri.de',
            amount=u'23'
        )
        new_abo.linkcode = u'ABCDEFGHIJKAbo'
        DBSession.add(new_abo)
        DBSession.flush()
        assert(new_abo.id == 2)
        request = testing.DummyRequest()
        #print type(new_abo.linkcode)
        request.matchdict['abo_id'] = new_abo.id  # does exist
        from pyramid_mailer import get_mailer
        mailer = get_mailer(request)
        result = send_mail_view(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject,
            u"You sustain C3S: Deine Links!")
        #print dir(mailer.outbox[0])
        self.assertTrue(new_abo.linkcode in mailer.outbox[0].body)
        #print result.location
        self.assertTrue('dash' in result.location)  # redirected

    def test_mail_utils(self):
        from zabo.mail_utils import mailbody_transfer_received
        # first, create an abo in the DB and thus an id to match
        new_abo = Abo(
            name=u'foobar',
            email=u'foo@shri.de',
            amount=u'23'
        )
        new_abo.linkcode = u'ABCDEFGHIJKAbo'
        new_abo.locale = u'de'
        DBSession.add(new_abo)
        DBSession.flush()
        assert(new_abo.id == 2)
        old_abo = Abo.get_by_id(1)
        old_abo.locale = u'en'
        _url = 'http://foobar.com'
        # englisch
        result1 = mailbody_transfer_received(old_abo, _url)
        #print result1
        self.assertTrue('Hello' in result1)

        # german
        result2 = mailbody_transfer_received(new_abo, _url)
        #print result2
        self.assertTrue('Hallo' in result2)
        #assert(new_abo.id == 4)


class TestSomeFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_models_sponsorshipGrade_helperFunction(self):
        from zabo.models import sponsorshipGrade
        #print 
        self.assertTrue(sponsorshipGrade(1) == '0')
        self.assertTrue(sponsorshipGrade(4) == '0')
        self.assertTrue(sponsorshipGrade(5) == '1')
        self.assertTrue(sponsorshipGrade(6) == '2')
        self.assertTrue(sponsorshipGrade(14) == '2')
        self.assertTrue(sponsorshipGrade(15) == '3')
        self.assertTrue(sponsorshipGrade(29) == '3')
        self.assertTrue(sponsorshipGrade(30) == '4')
        self.assertTrue(sponsorshipGrade(49) == '4')
        self.assertTrue(sponsorshipGrade(50) == '5')
        self.assertTrue(sponsorshipGrade(99) == '5')
        self.assertTrue(sponsorshipGrade(100) == '6')
        self.assertTrue(sponsorshipGrade(12345) == '6')
