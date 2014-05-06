#!/bin/env/python
# -*- coding: utf-8 -*-
# http://docs.pylonsproject.org/projects/pyramid/dev/narr/testing.html
#                                            #creating-functional-tests
#from datetime import date
from logging import getLogger
#import os
from sqlalchemy import engine_from_config
import transaction
from pyramid import testing
import unittest

from zabo.models import (
    DBSession,
    Base,
    Abo,
    Staff,
    Group,
)

log = getLogger(__name__)


class ZaboTestBase(unittest.TestCase):
    """
    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    they also serve to get coverage for 'main'
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.close()
            DBSession.remove()
            #print "closed and removed DBSession"
        except:
            pass
            #print "no session to close"
        #try:
        #    os.remove('test_webtest_accountants.db')
        #    #print "deleted old test database"
        #except:
        #    pass
        #    #print "never mind"
        # self.session = DBSession()
        my_settings = {
            #'sqlalchemy.url': 'sqlite:///test_webtest_accountants.db',
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'zabo.dashboard_number': '32',
            'foo': 'bar',
            'mailrecipient': 'c@c3s.cc',
            'pyramid.includes' : 'pyramid_mailer.testing',
            #u'zabo.mail_rec': u'c@c3s.cc',
            #'zabo.mail_rec': 'c@c3s.cc',
            #'mail_rec': 'c@c3s.cc',
        }
        #self.config.add_settings({'zabo.mail_rec': 'c@c3s.cc'})
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        self._insert_abos()

        with transaction.manager:
                # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            try:
                DBSession.add(accountants_group)
                DBSession.flush()
                #print("adding group staff")
            except:
                print("could not add group staff.")
                # pass
            # staff personnel
            staffer1 = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
            )
            staffer1.groups = [accountants_group]
            try:
                DBSession.add(accountants_group)
                DBSession.add(staffer1)
                DBSession.flush()
            except:
                print("could not add staffer1")
                # pass

        from zabo import main
        app = main({}, **my_settings)
        from webtest import TestApp
        self.testapp = TestApp(app)
        #print "has key?"
        #print (self.testapp.app.registry.settings.has_key('mailrecipient'))
        #self.testapp.app.registry.settings['mailrecipient'] = 'c@c3s.cc'
        #self.testapp.app.registry.settings['mailrecipient'] = 'c@c3s.cc'
        #print self.testapp.app.registry.settings
        #print dir(self.testapp.app.registry.settings)
        #print "has key?"
        #print (self.testapp.app.registry.settings.has_key('mailrecipient'))


    def tearDown(self):
        DBSession.close()
        DBSession.remove()
        #os.remove('test_webtest_accountants.db')
        testing.tearDown()

    def _insert_abos(self):
        with transaction.manager:
            abo1 = Abo(  # german
                name=u'SomeAliasnäme',
                email=u'some@shri.de',
                amount=u'23',
            )
            abo2 = Abo(  # german
                name=u'AAASomeFirstnäme',
                email=u'abo2@shri.de',
                amount=u'42',
            )
            DBSession.add(abo1)
            DBSession.add(abo2)
            DBSession.flush()


class FrontendFunctionalTests(ZaboTestBase):

    def test_zabo(self):
        """
        load the abo form, submit, re-edit, submit, confirm, done.
        """
        res = self.testapp.get('/abo', status=200)
        self.failUnless('Zuschuss' in res.body)
        self.failUnless('Name oder Alias' in res.body)
        self.failUnless('Email' in res.body)
        self.failUnless('Betrag (in ganzen €)' in res.body)
        self.failUnless('Eingaben prüfen' in res.body)
        self.failUnless('Copyright © C3S SCE mbh' in res.body)
        #self.failUnless('' in res.body)

        form = res.form
        form['name'] = 'foos'
        res2 = form.submit('submit')
        self.failUnless(
            'There was a problem with your submission' in res2.body)
        form['email'] = 'foo@bar.com'
        res2 = form.submit('submit')
        self.failUnless(
            'There was a problem with your submission' in res2.body)
#        form['email'] = ''

        form['amount'] = 'foo'
        res2 = form.submit('submit')
        self.failUnless(
            'There was a problem with your submission' in res2.body)
        self.failUnless('"foo" is not a number' in res2.body)

        form['amount'] = '4'
        res2 = form.submit('submit')
        self.failUnless(
            'There was a problem with your submission' in res2.body)
        form['amount'] = '5'
        res2 = form.submit('submit')
        res2 = res2.follow()
        '''
        we have all fields field and should be taken to the confirm page
        '''
        self.failUnless('Eingaben bestätigen' in res2.body)
        self.failUnless('Eingaben verändern' in res2.body)
        self.failUnless('Name oder Alias' in res2.body)
        self.failUnless('foos' in res2.body)
        self.failUnless('Email' in res2.body)
        self.failUnless('foo@bar.com' in res2.body)
        self.failUnless('Betrag' in res2.body)
        self.failUnless('5' in res2.body)

        '''say we want to change some info before confirmation: re-edit'''
        res2 = form.submit('re-edit')
        self.failIf('Eingaben bestätigen' in res2.body)
        #print res2.body

        form = res2.form
        form['name'] = 'foos1'
        res3 = form.submit('submit')
        #        res2 = res2.follow()
        self.failUnless(
            'The resource was found at http://localhost/confirm; '
            'you should be redirected automatically.' in res3.body)

        res3 = res3.follow()  # follow redirect
        #print res3.body
        self.failUnless('foos1' in res3.body)

        form = res3.form
        #print '#'*60
        #print type(res3.request)
        #print dir(res3.request)
        #self.testapp.app.registry.settings['mailrecipient'] = 'c@c3s.cc'
        from pyramid_mailer import get_mailer
        mailer = get_mailer(self.testapp.app.registry)
        #mailer = get_mailer(res3.request)
        #print mailer
        #print dir(mailer)

        res4 = form.submit('sendmail')
        #print res4.body
        self.failUnless(
            'The resource was found at http://localhost/done; '
            'you should be redirected automatically.' in res4.body)
        res5 = res4.follow()
        #print res5
        #print dir(mailer)
        #print type(mailer)
        #self.assertTrue(len(mailer.outbox) == 2)
        #print "res5.body: {}".format(res5.body)

        #self.failUnless('just let this test fail' in res4.body)

    def test_unsolicited_confirm_view(self):
        """
        try to load the confirm page, be redirected to the form
        """
        res = self.testapp.get('/confirm', status=302)
        self.failUnless(
            'The resource was found at http://localhost/abo' in res.body)
        #log.info('foo')
        #print res2.body
        #
        #print dir(form)

    def test_unsolicited_sendmail_view(self):
        """
        try to load the sendmail page, be redirected to the form
        """
        res = self.testapp.get('/done', status=302)
        self.failUnless(
            'The resource was found at http://localhost/abo' in res.body)
        #log.info('foo')
        #print res2.body
        #
        #print dir(form)


class StatisticsFunctionalTests(ZaboTestBase):

    def test_stats_view(self):
        """
        login and go to stats view
        """
        # login
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try invalid user
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res3 = form.submit('submit', status=302)
        #
        # being logged in ...
        res4 = res3.follow()
        self.failUnless(
            'Dashboard' in res4.body)
        # now that we are logged in, test logout
        res = self.testapp.get('/stats', status=200)
        print res.body

        self.failUnless('2 DB-Einträge' in res.body)
        self.failUnless('65 Euro, die noch nicht bezahlt sind.' in res.body)
        self.failUnless('0 Euro, die schon bezahlt sind.' in res.body)
        #self.failUnless('no no no' in res.body)


class SponsorsFunctionalTests(ZaboTestBase):

    def test_page_nonexisting_linkcode(self):
        '''
        try to load a apage with a non-existing linkcode
        '''
        res = self.testapp.get('/sponsor/NONEXISTING.html', status=200)
        print res.body
        self.failUnless('this link code is invalid.' in res.body)

    def test_image_nonexisting_linkcode(self):
        '''
        try to load a apage with a non-existing linkcode
        '''
        res = self.testapp.get('/sponsor/NONEXISTING.png', status=302)
        self.failUnless('badge_invalid.png' in res.location)
        res2 = res.follow()
        #print len(res2.body)
        self.failUnless(4000 < len(res2.body) < 4500)  # check size of image

    def test_html_and_png(self):
        """
        load the page and image for use by the sponsor
        """
        # make
        from zabo.models import Abo
        new_abo = Abo(
            name=u'oleander',
            email=u'ole@shri.de',
            amount=u'23',
        )
        # set the linkcode to sth, which is usually done via button in backend
        new_abo.linkcode = u'YES_THIS_ONE'
        DBSession.add(new_abo)
        DBSession.flush()

        '''
        image
        '''
        image = self.testapp.get(
            '/sponsor/{}.png'.format(new_abo.linkcode), status=200)
        print len(image.body)
        self.failUnless(4500 < len(image.body) < 5000)  # check size of image
        '''
        html page
        '''
        html = self.testapp.get(
            '/sponsor/{}.html'.format(new_abo.linkcode), status=200)
        #print html.body
        # link to image must be in html
        self.failUnless(
            '/sponsor/{}.png'.format(new_abo.linkcode) in html.body)
        self.failUnless(
            'Name: {}<br />'.format(new_abo.name) in html.body)

        #self.failUnless('no no no' in res.body)


class BackendFunctionalTests(ZaboTestBase):

    def test_login_and_logout(self):
        """
        load the login form, dashboard, member detail
        """
        #
        # login
        #
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try invalid user
        form = res.form
        form['login'] = 'foo'
        form['password'] = 'bar'
        res2 = form.submit('submit')
        self.failUnless(
            'Please note: There were errors' in res2.body)
        # try valid user & invalid password
        form = res2.form
        form['login'] = 'rut'
        form['password'] = 'berry'
        res3 = form.submit('submit', status=200)
        # try valid user, valid password
        form = res2.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res3 = form.submit('submit', status=302)
        #
        # being logged in ...
        res4 = res3.follow()
        #res4 = res4.follow()
        #print(res4.body)
        self.failUnless('Dashboard' in res4.body)

        # once we are already logged in, the login redirects to the dashboard
        res = self.testapp.get('/login', status=302)
        res2 = res.follow()
        self.failUnless('Dashboard' in res2.body)

         # now that we are logged in, test logout
        res = self.testapp.get('/logout', status=302)
        res2 = res.follow()
        self.failUnless('login' in res2.body)

    def _login_and_dashboard(self):
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        res3 = res2.follow()
        self.failUnless('Dashboard' in res3.body)

    def test_login_and_dashboard(self):
        self._login_and_dashboard()

    def test_payment_received(self):
        '''
        test the 'payment_received' view in backend_views.py

        login, go to dashboard,
        where the buttons to toggle reception of payment are located.
        '''
        self._login_and_dashboard()
        res = self.testapp.get('/login', status=302)
        res3 = res.follow()
        self.failUnless('Dashboard' in res3.body)
        #print res3.body

        '''
        set to yes
        '''
        res = self.testapp.get('/paym_recd/2', status=302)
        res2 = res.follow()
        #print res2.body
        self.failUnless('class="btn btn-default">ok</a>' in res2.body)
        abo2 = Abo.get_by_id(2)
        self.assertEquals(abo2.payment_received, True)
        #print abo2.linkcode
        #print type(abo2.name)
        _url = '/sponsor/' + abo2.linkcode + '.html'
        _html = self.testapp.get(_url, status=200)
        #print _html.body
        #self.assertTrue(abo2.name in _html.body)
        self.assertTrue(str(abo2.amount) in _html.body)
        self.assertTrue(str(abo2.linkcode) in _html.body)

        '''
        set to no
        '''
        res = self.testapp.get('/paym_recd/2', status=302)
        res2 = res.follow()
        self.failUnless('class="btn btn-primary">Noch nicht?</a>' in res2.body)
        abo2 = Abo.get_by_id(2)
        self.assertEquals(abo2.payment_received, False)
        _html = self.testapp.get(_url, status=200)
        #print _html.body
        #self.assertTrue(abo2.name in _html.body)
        self.assertTrue(str(abo2.amount) in _html.body)
        self.assertTrue(str(abo2.linkcode) in _html.body)

        #self.failUnless('this wont exist' in res3.body)

    def test_send_mail_view(self):
        '''
        test the 'send_mail_view' view in backend_views.py

        login, go to dashboard,
        where the buttons to send the mail are located.
        '''
        self._login_and_dashboard()
        res = self.testapp.get('/login', status=302)
        res3 = res.follow()
        self.failUnless('Dashboard' in res3.body)

        '''
        set to yes
        '''
        # try with invalid id, be redirected to dashboard
        res = self.testapp.get('/mail_mail_conf/foobar', status=302)
        res2 = res.follow()
        self.failUnless('Dashboard' in res2.body)

        res = self.testapp.get('/mail_mail_conf/2', status=302)
        res2 = res.follow()
        #print res2.body
        self.failUnless('class="btn btn-default">ok</a>' in res2.body)
        abo2 = Abo.get_by_id(2)
        #print "abo2.payment_confirmed_email: {}".format(
        #    abo2.payment_confirmed_email)
        self.assertEquals(abo2.payment_confirmed_email, True)

    def test_delete_entry_view(self):
        self._login_and_dashboard()
        res = self.testapp.get('/login', status=302)
        res3 = res.follow()
        self.failUnless('Dashboard' in res3.body)

        number = Abo.get_number()
        left = number
        print "# Abos in DB: {}".format(number)

        for i in range(1, number+1):
            print "the i: {}".format(i)
            res = self.testapp.get('/del_entry/{}'.format(i), status=302)
            left += -1
            self.assertEqual(Abo.get_number(), left)

        # check there are no items left in the DB
        self.assertEqual(Abo.get_number(), 0)

    # DASHBOARD SORTING
    def test_dashboard_code_to_show(self):
        pass

    def test_dashboard_num_to_show(self):
        pass

#         # choose number of applications shown
#         res6a = self.testapp.get(
#             '/dashboard',
#             status=302,
#             extra_environ={
#                 'num_display': '30',
#             }
#         )
#         res6a = res6a.follow()

#         self.failUnless('<h1>Dashboard</h1>' in res6a.body)
#         res6a = self.testapp.get(
#             '/dashboard/1/id/asc', status=200,
#         )

#         self.failUnless('<h1>Dashboard</h1>' in res6a.body)
#         # try an invalid page number
#         res6b = self.testapp.get(
#             '/dashboard/foo/bar/baz',
#             status=200,
#         )

#         self.failUnless(
#             '<p>Number of data sets:' in res6b.body)

#         # change the number of items to show
#         form = res6b.forms[1]
#         form['num_to_show'] = "42"  # post a number: OK
#         resX = form.submit('submit', status=200)

#         form = resX.forms[1]
#         form['num_to_show'] = "mooo"  # post a string: no good
#         resY = form.submit('submit', status=200)

#         #import pdb; pdb.set_trace()
#         # member details
#         #
#         # now look at some members details with nonexistant id
#         res7 = self.testapp.get('/detail/5000', status=302)
#         res7a = res7.follow()
#         res7a = res7a.follow()
#         self.failUnless('Dashboard' in res7a.body)

#         # now look at some members details
#         res7 = self.testapp.get('/detail/1', status=200)
#         self.failUnless('Firstnäme' in res7.body)
#         self.failUnless(
#             "<td>signature received?</td><td>No</td>" in res7.body)
#         self.failUnless(
#             "<td>payment received?</td><td>No</td>" in res7.body)

#         # form = res7.form
#         # form['signature_received'] = True
#         # form['payment_received'] = True
#         # res8 = form.submit('submit')
#         # #print(res8.body)
#         # self.failUnless(
#         #     "<td>signature received?</td><td>True</td>" in res8.body)
#         # self.failUnless(
#         #     "<td>payment received?</td><td>True</td>" in res8.body)
#         ################################################################
#         # now we change some of the details: switch signature status
#         # via http-request rather than the form
#         resD1 = self.testapp.get('/detail/1', status=200)  # look at details
#         #print resD1.body
#         self.assertTrue(
#             "<td>signature received?</td><td>No</td>" in resD1.body)
#         self.assertTrue(
#             "<td>payment received?</td><td>No</td>" in resD1.body)
#         #
#         # switch signature
#         resD2a = self.testapp.get('/switch_sig/1', status=302)  # # # # # OFF
#         resD2b = resD2a.follow()  # we are taken to the dashboard
#         resD2b = self.testapp.get('/detail/1', status=200)
#         #print resD2b.body
#         self.assertTrue(
#             "<td>signature received?</td><td>True</td>" in resD2b.body)
#         resD2a = self.testapp.get('/switch_sig/1', status=302)  # # # # # ON
#         resD2b = resD2a.follow()  # we are taken to the dashboard
#         resD2b = self.testapp.get('/detail/1', status=200)
#         self.assertTrue(
#             "<td>signature received?</td><td>No</td>" in resD2b.body)
#         #
#         # switch payment
#         resD3a = self.testapp.get('/switch_pay/1', status=302)  # # # # OFF
#         resD3b = resD3a.follow()  # we are taken to the dashboard
#         resD3b = self.testapp.get('/detail/1', status=200)
#         print resD3b.body
#         self.assertTrue(
#             "<td>payment received?</td><td>True</td>" in resD3b.body)
#         resD3a = self.testapp.get('/switch_pay/1', status=302)  # # # # ON
#         resD3b = resD3a.follow()  # we are taken to the dashboard
#         resD3b = self.testapp.get('/detail/1', status=200)
#         self.assertTrue(
#             "<td>payment received?</td><td>No</td>" in resD3b.body)
#         #
#         ####################################################################
#         # delete an entry
#         resDel1 = self.testapp.get('/dashboard/0/id/asc', status=200)

# #        self.failUnless(
# #            '      <p>Number of data sets: 1</p>' in resDel1.body.splitlines())
#         resDel2 = self.testapp.get('/delete/1', status=302)
#         resDel3 = resDel2.follow()
#         resDel3 = resDel3.follow()
#         self.failUnless('was deleted' in resDel3.body)

#         # finally log out ##################################################
#         res9 = self.testapp.get('/logout', status=302)  # redirects to login
#         res10 = res9.follow()
#         self.failUnless('login' in res10.body)

#     def test_dashboard_orderByIdAsc_dashboardOrdered(self):
#         res = self._login()
#         res2 = self.testapp.get('/dashboard/0/id/asc')
#         pq = self._get_pyquery(res2.body)
#         # column-order: id code firstname lastname
#         first_member_row = pq('tr:nth-child(2)')
#         id_ = first_member_row('td:nth-child(1)')
#         self.assertEqual('1', id_.text())

#     def test_dashboard_orderByIdDesc_dashboardOrdered(self):
#         res = self._login()
#         res2 = self.testapp.get('/dashboard/0/id/desc')
#         pq = self._get_pyquery(res2.body)
#         first_member_row = pq('tr:nth-child(2)')
#         id_ = first_member_row('td:nth-child(1)')
#         self.assertEqual('3', id_.text())

#     def test_dashboard_orderByFirstnameAsc_dashboardOrdered(self):
#         res = self._login()
#         res2 = self.testapp.get('/dashboard/0/firstname/asc')
#         pq = self._get_pyquery(res2.body)
#         first_member_row = pq('tr:nth-child(2)')
#         first_name = first_member_row('td:nth-child(3)')
#         self.assertEqual(u'AAASomeFirstnäme', first_name.text())

#     def test_dashboard_orderByFirstnameDesc_dashboardOrdered(self):
#         res = self._login()
#         res2 = self.testapp.get('/dashboard/0/firstname/desc')
#         pq = self._get_pyquery(res2.body)
#         first_member_row = pq('tr:nth-child(2)')
#         first_name = first_member_row('td:nth-child(3)')
#         self.assertEqual(u'SomeFirstnäme', first_name.text())

#     def test_dashboard_orderByLastnameAsc_dashboardOrdered(self):
#         res = self._login()
#         res2 = self.testapp.get('/dashboard/0/lastname/asc')
#         pq = self._get_pyquery(res2.body)
#         first_member_row = pq('tr:nth-child(2)')
#         last_name = first_member_row('td:nth-child(4)')
#         self.assertEqual(u'AAASomeLastnäme', last_name.text())

#     def test_dashboard_orderByLastnameDesc_dashboardOrdered(self):
#         self._login()
#         res2 = self.testapp.get('/dashboard/0/lastname/desc')
#         pq = self._get_pyquery(res2.body)
#         first_member_row = pq('tr:nth-child(2)')
#         last_name = first_member_row('td:nth-child(4)')
#         self.assertEqual(u'XXXSomeLastnäme', last_name.text())

#     def test_dashboard_afterDelete_sameOrderAsBefore(self):
#         self._login()
#         self.testapp.get('/dashboard/0/lastname/asc')  # To set cookie with order and orderby
#         resdel = self.testapp.get('/delete/3')  # Delete member with lastname AAASomeLastnäme
#         resdel = resdel.follow()
#         resdel = resdel.follow()
#         pq = self._get_pyquery(resdel.body)
#         first_member_row = pq('tr:nth-child(2)')
#         last_name = first_member_row('td:nth-child(4)')
#         self.assertEqual(u'SomeLastnäme', last_name.text())

#     def test_dashboard_afterDelete_messageShown(self):
#         self._login()
#         resdel = self.testapp.get('/delete/1')
#         resdel = resdel.follow()
#         resdel = resdel.follow()
#         pq = self._get_pyquery(resdel.body)
#         message = pq('#message').text()
#         self.assertTrue('was deleted' in message)

#     def test_dashboard_onFirstPage_noPreviousLinkShown(self):
#         self._login()
#         self._change_num_to_show("1")
#         res = self.testapp.get('/dashboard/0/id/desc')
#         pq = self._get_pyquery(res.body)
#         self.assertTrue(len(pq("#navigate_previous")) == 0)

#     def test_dashboard_onFirstPage_nextLinkShown(self):
#         self._login()
#         self._change_num_to_show("1")
#         res = self.testapp.get('/dashboard/0/id/desc')
#         pq = self._get_pyquery(res.body)
#         self.assertTrue(len(pq("#navigate_next")) == 1)

#     def test_dashboard_onSomePage_nextPreviousLinkShown(self):
#         self._login()
#         self._change_num_to_show("1")
#         res = self.testapp.get('/dashboard/1/id/desc')
#         pq = self._get_pyquery(res.body)
#         self.assertTrue(len(pq("#navigate_next")) == 1)
#         self.assertTrue(len(pq("#navigate_previous")) == 1)

#     def test_dashboard_onLastPage_previousLinkShown(self):
#         self._login()
#         self._change_num_to_show("1")
#         res = self.testapp.get('/dashboard/3/id/desc')
#         pq = self._get_pyquery(res.body)
#         self.assertTrue(len(pq("#navigate_previous")) == 1)

#     def test_dashboard_onLastPage_noNextLinkShown(self):
#         self._login()
#         self._change_num_to_show("1")
#         res = self.testapp.get('/dashboard/3/id/desc')
#         pq = self._get_pyquery(res.body)
#         self.assertTrue(len(pq("#navigate_next")) == 0)

#     def _get_pyquery(self, html):
#         from pyquery import PyQuery as pq
#         pure_html = ''.join(html.split('\n')[2:])
#         pure_html = "<html>" + pure_html
#         d = pq(pure_html)
#         return d

#     def _login(self):
#         res = self.testapp.get('/login', status=200)
#         self.failUnless('login' in res.body)
#         # try valid user, valid password
#         form = res.form
#         form['login'] = 'rut'
#         form['password'] = 'berries'
#         res2 = form.submit('submit', status=302)
#         #
#         # being logged in ...
#         res3 = res2.follow()
#         res3 = res3.follow()
#         self.failUnless('Dashboard' in res3.body)
#         return res3

#     def _change_num_to_show(self, num_to_show="1"):
#         res = self.testapp.get('/dashboard/0/id/desc')
#         form = res.forms[1]
#         form['num_to_show'] = num_to_show
#         resX = form.submit('submit', status=200)
#         return resX

#     def test_dashboard_search_code(self):
#         """
#         load the dashboard and search for confirmation code
#         """
#         #
#         # login
#         #
#         res3 = self._login()

#         """
#         we fill the confirmation code search form with a valid code,
#         submit the form
#         and check results
#         """
#         # try invalid code
#         form = res3.forms[0]
#         form['code_to_show'] = 'foo'
#         res = form.submit()
#         self.failUnless('Dashboard' in res.body)
#         # now use existing code
#         form = res.forms[0]
#         form['code_to_show'] = 'ABCDEFGFOO'
#         res = form.submit()
#         self.failIf('Dashboard' in res.body)

#     def test_dashboard_regenerate_pdf(self):
#         """
#         load the dashboard and regenerate a PDF
#         """
#         #
#         # login
#         #
#         res = self.testapp.get('/login', status=200)
#         self.failUnless('login' in res.body)
#         # try valid user, valid password
#         form = res.form
#         form['login'] = 'rut'
#         form['password'] = 'berries'
#         res2 = form.submit('submit', status=302)
#         #
#         # being logged in ...
#         res3 = res2.follow()
#         res3 = res3.follow()
#         self.failUnless('Dashboard' in res3.body)

#         """
#         try to load a users PDF
#         check size
#         """
#         # try invalid code
#         pdf = self.testapp.get('/re_C3S_SCE_AFM_WRONGCODE.pdf')
#         self.failUnless('The resource was found at' in pdf.body)
#         pdf = self.testapp.get('/re_C3S_SCE_AFM_ABCDEFGFOO.pdf')
#         # now use existing code
#         self.failUnless(80000 < len(pdf.body) < 150000)  # check pdf size

#     def test_dashboard_mail_signature_confirmation(self):
#         """
#         load the dashboard and send out confirmation mails
#         """
#         #
#         # login
#         #
#         res = self.testapp.get('/login', status=200)
#         self.failUnless('login' in res.body)
#         # try valid user, valid password
#         form = res.form
#         form['login'] = 'rut'
#         form['password'] = 'berries'
#         res2 = form.submit('submit', status=302)
#         #
#         # being logged in ...
#         res3 = res2.follow()
#         res3 = res3.follow()

#         self.failUnless('Dashboard' in res3.body)

#         """
#         try to send out the signature confirmation email
#         """
#         # try invalid code
#         pdf = self.testapp.get('/re_C3S_SCE_AFM_WRONGCODE.pdf')
#         self.failUnless('The resource was found at' in pdf.body)
#         pdf = self.testapp.get('/re_C3S_SCE_AFM_ABCDEFGFOO.pdf')
#         # now use existing code
#         self.failUnless(80000 < len(pdf.body) < 150000)  # check pdf size


# class FunctionalTests2(unittest.TestCase):
#     """
#     these tests are functional tests to check functionality of the whole app
#     (i.e. integration tests)
#     they also serve to get coverage for 'main'
#     """
#     def setUp(self):
#         self.config = testing.setUp()
#         self.config.include('pyramid_mailer.testing')
#         try:
#             DBSession.close()
#             DBSession.remove()
#             #print("removed old DBSession ===================================")
#         except:
#             #print("no DBSession to remove ==================================")
#             pass
#         #try:
#         #    os.remove('test_webtest_functional.db')
#         #    #print "deleted old test database"
#         #except:
#         #    pass
#         #    #print "never mind"

#         my_settings = {
#             #'sqlalchemy.url': 'sqlite:///test_webtest_functional.db',
#             'sqlalchemy.url': 'sqlite:///:memory:',
#             'available_languages': 'da de en es fr',
#             'c3smembership.mailaddr': 'c@c3s.cc'}
#         engine = engine_from_config(my_settings)
#         DBSession.configure(bind=engine)
#         self.session = DBSession  # ()

#         Base.metadata.create_all(engine)
#         # dummy database entries for testing
#         with transaction.manager:
#             abo1 = Abo(  # german
#                 name=u'SomeFirstnäme',
#                 email=u'some@shri.de',
#                 amount=u'23',
#             )
#             DBSession.add(abo1)
#             DBSession.flush()

#         from zabo import main
#         app = main({}, **my_settings)

#         from webtest import TestApp
#         self.testapp = TestApp(app)

#     def tearDown(self):
#         self.session.close()
#         self.session.remove()
#         #os.remove('test_webtest_functional.db')

#     def test_base_template(self):
#         """load the front page, check string exists"""
#         res = self.testapp.get('/', status=200)
#         self.failUnless('Cultural Commons Collecting Society' in res.body)
#         self.failUnless(
#             'Copyright 2013, C3S SCE' in res.body)

#     # def test_faq_template(self):
#     #     """load the FAQ page, check string exists"""
#     #     res = self.testapp.get('/faq', status=200)
#     #     self.failUnless('FAQ' in res.body)
#     #     self.failUnless(
#     #         'Copyright 2013, OpenMusicContest.org e.V.' in res.body)

#     def test_lang_en_LOCALE(self):
#         """load the front page, forced to english (default pyramid way),
#         check english string exists"""
#         res = self.testapp.reset()  # delete cookie
#         res = self.testapp.get('/?_LOCALE_=en', status=200)
#         self.failUnless(
#             'Application for Membership of ' in res.body)

#     def test_lang_en(self):
#         """load the front page, set to english (w/ pretty query string),
#         check english string exists"""
#         res = self.testapp.reset()  # delete cookie
#         res = self.testapp.get('/?en', status=302)
#         self.failUnless('The resource was found at' in res.body)
#         # we are being redirected...
#         res1 = res.follow()
#         self.failUnless(
#             'Application for Membership of ' in res1.body)

# # so let's test the app's obedience to the language requested by the browser
# # i.e. will it respond to http header Accept-Language?

#     # def test_accept_language_header_da(self):
#     #     """check the http 'Accept-Language' header obedience: danish
#     #     load the front page, check danish string exists"""
#     #     res = self.testapp.reset()  # delete cookie
#     #     res = self.testapp.get('/', status=200,
#     #                            headers={
#     #             'Accept-Language': 'da'})
#     #     #print(res.body) #  if you want to see the pages source
#     #     self.failUnless(
#     #         '<input type="hidden" name="_LOCALE_" value="da"' in res.body)

#     def test_accept_language_header_de_DE(self):
#         """check the http 'Accept-Language' header obedience: german
#         load the front page, check german string exists"""
#         res = self.testapp.reset()  # delete cookie
#         res = self.testapp.get(
#             '/', status=200,
#             headers={
#                 'Accept-Language': 'de-DE'})
#         #print(res.body) #  if you want to see the pages source
#         self.failUnless(
#             'Mitgliedschaftsantrag für die' in res.body)
#         self.failUnless(
#             '<input type="hidden" name="_LOCALE_" value="de"' in res.body)

#     def test_accept_language_header_en(self):
#         """check the http 'Accept-Language' header obedience: english
#         load the front page, check english string exists"""
#         res = self.testapp.reset()  # delete cookie
#         res = self.testapp.get(
#             '/', status=200,
#             headers={
#                 'Accept-Language': 'en'})
#         #print(res.body) #  if you want to see the pages source
#         self.failUnless(
#             "I want to become"
#             in res.body)

#     # def test_accept_language_header_es(self):
#     #     """check the http 'Accept-Language' header obedience: spanish
#     #     load the front page, check spanish string exists"""
#     #     res = self.testapp.reset()  # delete cookie
#     #     res = self.testapp.get('/', status=200,
#     #                            headers={
#     #             'Accept-Language': 'es'})
#     #     #print(res.body) #  if you want to see the pages source
#     #     self.failUnless(
#     #         'Luego de enviar el siguiente formulario,' in res.body)

#     # def test_accept_language_header_fr(self):
#     #     """check the http 'Accept-Language' header obedience: french
#     #     load the front page, check french string exists"""
#     #     res = self.testapp.reset()  # delete cookie
#     #     res = self.testapp.get('/', status=200,
#     #                            headers={
#     #             'Accept-Language': 'fr'})
#     #     #print(res.body) #  if you want to see the pages source
#     #     self.failUnless(
#     #         'En envoyant un courriel à data@c3s.cc vous pouvez' in res.body)

#     def test_no_cookies(self):
#         """load the front page, check default english string exists"""
#         res = self.testapp.reset()  # delete cookie
#         res = self.testapp.get(
#             '/', status=200,
#             headers={
#                 'Accept-Language': 'af, cn'})  # ask for missing languages
#         #print res.body
#         self.failUnless('Application for Membership' in res.body)

# #############################################################################
# # check for validation stuff

#     def test_form_lang_en_non_validating(self):
#         """load the join form, check english string exists"""
#         res = self.testapp.reset()
#         res = self.testapp.get('/?_LOCALE_=en', status=200)
#         form = res.form
#         #print(form.fields)
#         #print(form.fields.values())
#         form['firstname'] = 'John'
#         #form['address2'] = 'some address part'
#         res2 = form.submit('submit')
#         self.failUnless(
#             'There was a problem with your submission' in res2.body)

#     def test_form_lang_de(self):
#         """load the join form, check german string exists"""
#         res = self.testapp.get('/?de', status=302)
#         #print(res)
#         self.failUnless('The resource was found at' in res.body)
#         # we are being redirected...
#         res2 = res.follow()
#         #print(res2)
#         # test for german translation of template text (lingua_xml)
#         self.failUnless(
#             'Mitgliedschaftsantrag für die' in res2.body)
#         # test for german translation of form field label (lingua_python)
#         self.failUnless('Vorname' in res2.body)

#     def test_form_lang_LOCALE_de(self):
#         """load the join form in german, check german string exists
#         this time forcing german locale the pyramid way
#         """
#         res = self.testapp.get('/?_LOCALE_=de', status=200)
#         # test for german translation of template text (lingua_xml)
#         self.failUnless(
#             'Mitgliedschaftsantrag für die' in res.body)
#         # test for german translation of form field label (lingua_python)
#         self.failUnless('Vorname' in res.body)

# ###########################################################################
# # checking the success page that sends out email with verification link

#     def test_check_email_en_wo_context(self):
#         """try to access the 'check_email' page and be redirected
#         check english string exists"""
#         res = self.testapp.reset()
#         res = self.testapp.get('/check_email?en', status=302)
#         self.failUnless('The resource was found at' in res.body)
#         # we are being redirected...
#         res1 = res.follow()
#         #print(res1)
#         self.failUnless(
#             'Application for Membership of ' in str(
#                 res1.body),
#             'expected string was not found in web UI')

# ###########################################################################
# # checking the view that gets code and mail, asks for a password
#     def test_verify_email_en_w_bad_code(self):
#         """load the page in english,
#         be redirected to the form (data is missing)
#         check english string exists"""
#         res = self.testapp.reset()
#         res = self.testapp.get('/verify/foo@shri.de/ABCD-----', status=200)
#         self.failUnless(
#             'Password' in res.body)
#         form = res.form
#         form['password'] = 'foobar'
#         res2 = form.submit('submit')
#         self.failUnless(
#             'Password' in res2.body)

#     def test_verify_email_en_w_good_code(self):
#         """
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get('/verify/some@shri.de/ABCDEFGFOO', status=200)
#         self.failUnless(
#             'Password' in res.body)
#         form = res.form
#         form['password'] = 'arandompassword'
#         res2 = form.submit('submit')
#         # print res2.body
#         self.failUnless(
#             'C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf' in res2.body)
# #        import pdb
# #        pdb.set_trace()
#             #'Your Email has been confirmed, Firstnäme Lastname!' in res.body)
#         #res2 = self.testapp.get(
#         #    '/C3S_SCE_AFM_Firstn_meLastname.pdf', status=200)
#         #self.failUnless(len(res2.body) > 70000)

# ###########################################################################
# # checking the disclaimer

#     # def test_disclaimer_en(self):
#     #     """load the disclaimer in english (via query_string),
#     #     check english string exists"""
#     #     res = self.testapp.reset()
#     #     res = self.testapp.get('/disclaimer?en', status=302)
#     #     self.failUnless('The resource was found at' in res.body)
#     #     # we are being redirected...
#     #     res1 = res.follow()
#     #     self.failUnless(
#     #         'you may order your data to be deleted at any time' in str(
#     #             res1.body),
#     #         'expected string was not found in web UI')

#     # def test_disclaimer_de(self):
#     #     """load the disclaimer in german (via query_string),
#     #     check german string exists"""
#     #     res = self.testapp.reset()
#     #     res = self.testapp.get('/disclaimer?de', status=302)
#     #     self.failUnless('The resource was found at' in res.body)
#     #     # we are being redirected...
#     #     res1 = res.follow()
#     #     self.failUnless(
#     #         'Datenschutzerkl' in str(
#     #             res1.body),
#     #         'expected string was not found in web UI')

#     # def test_disclaimer_LOCALE_en(self):
#     #     """load the disclaimer in english, check english string exists"""
#     #     res = self.testapp.reset()
#     #     res = self.testapp.get('/disclaimer?_LOCALE_=en', status=200)
#     #     self.failUnless(
#     #         'you may order your data to be deleted at any time' in str(
#     #             res.body),
#     #         'expected string was not found in web UI')

#     # def test_disclaimer_LOCALE_de(self):
#     #     """load the disclaimer in german, check german string exists"""
#     #     res = self.testapp.reset()
#     #     res = self.testapp.get('/disclaimer?_LOCALE_=de', status=200)
#     #     self.failUnless(
#     #         'Datenschutzerkl' in str(
#     #             res.body),
#     #         'expected string was not found in web UI')

#     def test_success_wo_data_en(self):
#         """load the success page in english (via query_string),
#         check for redirection and english string exists"""
#         res = self.testapp.reset()
#         res = self.testapp.get('/success?en', status=302)
#         self.failUnless('The resource was found at' in res.body)
#         # we are being redirected...
#         res1 = res.follow()
#         #print(res1)
#         self.failUnless(  # check text on page redirected to
#             'Please fill out the form' in str(
#                 res1.body),
#             'expected string was not found in web UI')

#     def test_success_pdf_wo_data_en(self):
#         """
#         try to load a pdf (which must fail because the form was not used)
#         check for redirection to the form and test string exists
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get(
#             '/C3S_SCE_AFM_ThefirstnameThelastname.pdf',
#             status=302)
#         self.failUnless('The resource was found at' in res.body)
#         # we are being redirected...
#         res1 = res.follow()
#         #print(res1)
#         self.failUnless(  # check text on page redirected to
#             'Please fill out the form' in str(
#                 res1.body),
#             'expected string was not found in web UI')

#     # def test_success_w_data(self):
#     #     """
#     #     load the form, fill the form, (in one go via POST request)
#     #     check for redirection, push button to send verification mail,
#     #     check for 'mail was sent' message
#     #     """
#     #     res = self.testapp.reset()
#     #     res = self.testapp.get('/', status=200)
#     #     form = res.form
#     #     print '*'*80
#     #     print '*'*80
#     #     print '*'*80
#     #     print form.fields
#     #     res = self.testapp.post(
#     #         '/',  # where the form is served
#     #         {
#     #             'submit': True,
#     #             'firstname': 'TheFirstName',
#     #             'lastname': 'TheLastName',
#     #             'date_of_birth': '1987-06-05',
#     #             'address1': 'addr one',
#     #             'address2': 'addr two',
#     #             'postcode': '98765 xyz',
#     #             'city': 'Devilstown',
#     #             'country': 'AF',
#     #             'email': 'email@example.com',
#     #             'password': 'berries',
#     #             'num_shares': '42',
#     #             '_LOCALE_': 'en',
#     #             #'activity': set(
#     #             #    [
#     #             #        u'composer',
#     #             #        #u'dj'
#     #             #    ]
#     #             #),
#     #             'invest_member': 'yes',
#     #             'member_of_colsoc': 'yes',
#     #             'name_of_colsoc': 'schmoo',
#     #             #'opt_band': 'yes band',
#     #             #'opt_URL': 'http://yes.url',
#     #             #'noticed_dataProtection': 'yes'
#     #             'num_shares': '23',
#     #         },
#     #         #status=302,  # expect redirection to success page
#     #         status=200,  # expect redirection to success page
#     #     )

#     #     print(res.body)
#     #     self.failUnless('The resource was found at' in res.body)
#     #     # we are being redirected...
#     #     res2 = res.follow()
#     #     self.failUnless('Success' in res2.body)
#     #     #print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
#     #     #print res2.body
#     #     #print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
#     #     self.failUnless('TheFirstName' in res2.body)
#     #     self.failUnless('TheLastName' in res2.body)
#     #     self.failUnless('1987-06-05' in res2.body)
#     #     self.failUnless('addr one' in res2.body)
#     #     self.failUnless('addr two' in res2.body)
#     #     self.failUnless('Devilstown' in res2.body)
#     #     self.failUnless('email@example.com' in res2.body)
#     #     self.failUnless('schmoo' in res2.body)

#     #     # now check for the "mail was sent" confirmation
#     #     res3 = self.testapp.post(
#     #         '/check_email',
#     #         {
#     #             'submit': True,
#     #             'value': "send mail"
#     #         }
#     #     )
#     #     #print(res3)
#     #     self.failUnless(
#     #         'An email was sent, TheFirstName TheLastName!' in res3.body)

# #     def test_success_and_reedit(self):
# #         """
# #         submit form, check success, re-edit: are the values pre-filled?
# #         """
# #         res = self.testapp.reset()
# #         res = self.testapp.get('/', status=200)
# #         form = res.form
# #         form['firstname'] = 'TheFirstNäme'
# #         form['lastname'] = 'TheLastNäme'
# #         form['address1'] = 'addr one'
# #         form['address2'] = 'addr two'
# #         res2 = form.submit('submit')
# #         print res2.body
# # #                'submit': True,
# # #                'date_of_birth': '1987-06-05',
# # #                'address2': 'addr two',
# # #                'postcode': '98765 xyz',
# # #                'city': 'Devilstöwn',
# # #                'email': 'email@example.com',
# # #                'num_shares': '23',
# # #                '_LOCALE_': 'en',
# # #                #'activity': set(
# #                 #    [
# #                 #        'composer',
# #                 #        #u'dj'
# #                 #    ]
# #                 #),
# # #                'country': 'AF',
# # #                'membership_type': 'investing',
# # #                'member_of_colsoc': 'yes',
# # #                'name_of_colsoc': 'schmoö',
# #                 #'opt_band': 'yes bänd',
# #                 #'opt_URL': 'http://yes.url',
# #                 #'noticed_dataProtection': 'yes'

# # #            },
# # #            status=302,  # expect redirection to success page
# # #        )

#     #    print(res.body)
#     #     self.failUnless('The resource was found at' in res.body)
#     #     # we are being redirected...
#     #     res2 = res.follow()
#     #     self.failUnless('Success' in res2.body)
#     #     #print("success page: \n%s") % res2.body
#     #     #self.failUnless(u'TheFirstNäme' in (res2.body))

#     #     # go back to the form and check the pre-filled values
#     #     res3 = self.testapp.get('/')
#     #     #print(res3.body)
#     #     #print("edit form: \n%s") % res3.body
#     #     self.failUnless('TheFirstNäme' in res3.body)
#     #     form = res3.form
#     #     self.failUnless(form['firstname'].value == u'TheFirstNäme')

#     def test_email_confirmation(self):
#         """
#         test email confirmation form and PDF download
#         with a known login/dataset
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get('/verify/some@shri.de/ABCDEFGFOO', status=200)
#         # print(res.body)
#         form = res.form
#         form['password'] = 'arandompassword'
#         res2 = form.submit('submit')
#         #print res2.body
#         self.failUnless("Load your PDF..." in res2.body)
#         self.failUnless(
#             "/C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf" in res2.body)
#         # load the PDF, check size
#         res3 = self.testapp.get(
#             '/C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf',
#             status=200
#         )
#         #print("length of result: %s") % len(res3.body)
#         #print("body result: %s") % (res3.body)  # ouch, PDF content!
#         self.failUnless(80000 < len(res3.body) < 150000)  # check pdf size

#     def test_email_confirmation_wrong_mail(self):
#         """
#         test email confirmation with a wrong email
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get(
#             '/verify/NOTEXISTS@shri.de/ABCDEFGHIJ', status=200)
#         #print(res.body)
#         self.failUnless("Please enter your password." in res.body)
#         # XXX this test shows nothing interesting

#     def test_email_confirmation_wrong_code(self):
#         """
#         test email confirmation with a wrong code
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get('/verify/foo@shri.de/WRONGCODE', status=200)
#         #print(res.body)
#         self.failUnless("Please enter your password." in res.body)

#     def test_success_check_email(self):
#         """
#         test "check email" success page with wrong data:
#         this should redirect to the form.
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get('/check_email', status=302)

#         res2 = res.follow()
#         self.failUnless("Please fill out the form" in res2.body)

