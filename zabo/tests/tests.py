import unittest
import transaction

from pyramid import testing

from zabo.models import (
    DBSession,
    Abo,
)


class TestMyViewSuccessCondition(unittest.TestCase):
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

    def test_passing_view(self):
        from zabo.views import zform_view
        request = testing.DummyRequest()
        info = zform_view(request)
        #import pdb
        #pdb.set_trace()
        self.assertTrue('zform' in info)
        #self.assertEqual(info['project'], 'zabo')

    def test_send_mail_view(self):
        '''
        tests for the send_email_view view in backend_views.py
        '''
        from zabo.backend_views import send_mail_view
        self.config.add_route('dash', '/dash')
        '''
        if the requested id does not exist, redirect to the dashboard
        '''
        request = testing.DummyRequest()
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
            u"C3S ZuschussAbo: deine Links!")
        #print dir(mailer.outbox[0])
        self.assertTrue(new_abo.linkcode in mailer.outbox[0].body)
        #print result.location
        self.assertTrue('dash' in result.location)  # redirected

        #self.assertTrue('foobar' in result)

# class TestMyViewFailureCondition(unittest.TestCase):
#     def setUp(self):
#         self.config = testing.setUp()
#         from sqlalchemy import create_engine
#         engine = create_engine('sqlite://')
#         from .models import (
#             Base,
#         #    MyModel,
#         )
#         DBSession.configure(bind=engine)

#     def tearDown(self):
#         DBSession.remove()
#         testing.tearDown()

#     def test_failing_view(self):
#         from .views import zform_view
#         request = testing.DummyRequest()
#         info = zform_view(request)
#         #import pdb
#         #pdb.set_trace()
#         self.assertEqual(info.status_int, 500)
