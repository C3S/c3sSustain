# -*- coding: utf-8 -*-

import colander
import datetime
import deform
from deform import ValidationFailure
import logging
import math
from pyramid.httpexceptions import HTTPFound
from pyramid.security import (
    authenticated_userid,
    forget,
    remember,
)
from pyramid.view import view_config
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from types import NoneType

from .views import (
    _,
    zpt_renderer,
)
from mail_utils import mailbody_transfer_received
from .models import (
    Abo,
    Staff,
    Transfers,
    DBSession,
)
from .utils import make_random_linkcode

log = logging.getLogger(__name__)


@view_config(permission='view',
             route_name='logout')
def logout_view(request):
    """
    can be used to log a user/staffer off. "forget"
    """
    request.session.invalidate()
    request.session.flash(_(u'Logged out successfully.'))
    #print "logged out."
    headers = forget(request)
    return HTTPFound(location=request.route_url('login'),
                     headers=headers)


@view_config(renderer='templates/login.pt',
             route_name='login')
def accountants_login(request):
    """
    This view lets accountants log in
    """
    logged_in = authenticated_userid(request)
    #print("authenticated_userid: " + str(logged_in))

    #log.info("login by %s" % logged_in)

    if logged_in is not None:  # if user is already authenticated
        return HTTPFound(  # redirect her to the dashboard
            request.route_url('dash',
                              number=0,))

    class AccountantLogin(colander.MappingSchema):
        """
        colander schema for login form
        """
        login = colander.SchemaNode(
            colander.String(),
            title=_(u"login"),
            oid="login",
        )
        password = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=5, max=100),
            widget=deform.widget.PasswordWidget(size=20),
            title=_(u"password"),
            oid="password",
        )

    schema = AccountantLogin()

    form = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
        #use_ajax=True,
        renderer=zpt_renderer
    )

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        #print("the form was submitted")
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            print(e)

            request.session.flash(
                (u"Please note: There were errors, "
                 "please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{'form': e.render()}

        # get user and check pw...
        login = appstruct['login']
        password = appstruct['password']

        try:
            checked = Staff.check_password(login, password)
        except AttributeError:  # pragma: no cover
            checked = False
        if checked:
            log.info("password check for %s: good!" % login)
            headers = remember(request, login)
            log.info("logging in %s" % login)
            return HTTPFound(  # redirect to accountants dashboard
                location=request.route_url(  # after successful login
                    'dash',
                    number=0,
                    request=request),
                headers=headers)
        else:
            log.info("password check: failed.")

    html = form.render()
    return {'form': html, }


@view_config(renderer='templates/dashboard.pt',
             permission='manage',
             route_name='dash')
def dashboard_view(request):
    """
    This view lets accountants view subscriptions and set their status:
    has their payment arrived?
    """
    #print("who is it? %s" % request.user.login)
    _number_of_datasets = Abo.get_number()
    #print("request.matchdict['number']: %s" % request.matchdict['number'])
    try:  # check if
        # a page number was supplied with the URL
        _page_to_show = int(request.matchdict['number'])
        #print("page to show: %s" % _page_to_show)
    except:
        _page_to_show = 0
    # is it a number? yes, cast above
    #if not isinstance(_page_to_show, type(1)):
    #    _page_to_show = 0
    #print("_page_to_show: %s" % _page_to_show)

    # check for input from "find dataset by confirm code" form
    if 'code_to_show' in request.POST:
        #print("found code_to_show in POST: %s" % request.POST['code_to_show'])
        try:
            _code = request.POST['code_to_show']
            #print(_code)
            _entry = Abo.get_by_code(_code)
            #print(_entry)
            #print(_entry.id)

            return HTTPFound(
                location=request.route_url(
                    'abo_detail',
                    _id=_entry.id)
            )
        except:
            # choose default
            print("barf!")
            pass

    # how many to display on one page?
    """
    num_display determines how many items are to be shown on one page
    """
    #print request.POST
    if 'num_to_show' in request.POST:
        #print("found it in POST")
        try:
            _num = int(request.POST['num_to_show'])
            if isinstance(_num, type(1)):
                num_display = _num
        except:
            # choose default
            num_display = 20
    elif 'num_display' in request.cookies:
        #print("found it in cookie")
        num_display = int(request.cookies['num_display'])
    else:
        #print("setting default")
        num_display = request.registry.settings[
            'zabo.dashboard_number']
    #print("num_display: %s " % num_display)

    """
    base_offset helps us to minimize impact on the database
    when querying for results.
    we can choose just those results we need for the page to show
    """
    #try:
    base_offset = int(_page_to_show) * int(num_display)
    #print("base offset: %s" % base_offset)
    #except:
    #    base_offset = 0
    #    if 'base_offset' in request.session:
    #        base_offset = request.session['base_offset']
    #    else:
    #        base_offset = request.registry.settings['speedfunding.offset']

    #print "how many? {}".format(num_display)
    #print "base offset? {}".format(base_offset)
    # get data sets from DB
    _abos = Abo.abo_listing(
        'id', how_many=num_display, offset=base_offset)

    # calculate next-previous-navi
    next_page = (int(_page_to_show) + 1)
    if (int(_page_to_show) > 0):
        previous_page = int(_page_to_show) - 1
    else:
        previous_page = int(_page_to_show)
    _last_page = int(math.ceil(_number_of_datasets / int(num_display)))
    if next_page > _last_page:
        next_page = _last_page
    # store info about current page in cookie
    request.response.set_cookie('on_page', value=str(_page_to_show))
    request.response.set_cookie('num_display', value=str(num_display))
    _order = 'asc'  # stupid default
    request.response.set_cookie('order', value=str(_order))
    _order_by = 'id'  # stupid default
    request.response.set_cookie('orderby', value=str(_order_by))

    # store info about current page in cookie
    #request.response.set_cookie('on_page', value=str(_page_to_show))
    #print("num_display: %s" % num_display)
    request.response.set_cookie('num_display', value=str(num_display))

    # prepare a form for autocomplete search for reference codes.
    class RefcodeAutocompleteForm(colander.MappingSchema):
        """
        colander schema to make deform autocomplete form
        """
        code_to_show = colander.SchemaNode(
            colander.String(),
            title='Code finden (quicksearch; Groß-/Kleinschreibung beachten!)',
            validator=colander.Length(min=1, max=8),
            widget=deform.widget.AutocompleteInputWidget(
                min_length=1,
                #title="widget title",
                values=request.route_path(
                    'autocomplete_refcode_input_values',
                    traverse=('autocomplete_refcode_input_values')
                )
            ),
            description='start typing. use arrows. press enter. twice.'
        )

    schema = RefcodeAutocompleteForm()
    form = deform.Form(
        schema,
        buttons=('go!',),
        #use_ajax=True,  # <-- whoa!
        #renderer=zpt_renderer,
    )
    autoformhtml = form.render()

    return {'_number_of_datasets': _number_of_datasets,
            'abos': _abos,
            'num_display': num_display,
            'next': next_page,
            'previous': previous_page,
            'autoform': autoformhtml,
            'current': _page_to_show,
            'last_page': _last_page,
            'is_last_page': _page_to_show == _last_page,
            'is_first_page': _page_to_show == 0,
            'order': _order,
            'orderby': _order_by,
            }


@view_config(renderer='json',
             permission='manage',
             route_name='autocomplete_refcode_input_values')
def autocomplete_refcode_input_values(request):
    '''
    AJAX view/helper function
    returns the matching set of values for autocomplete/quicksearch

    this function and view expects a parameter 'term' (?term=foo) containing a
    string to find matching entries (e.g. starting with 'foo') in the database
    '''
    text = request.params.get('term', '')
    return Abo.get_matching_refcodes(text)


@view_config(renderer='templates/abo_detail.pt',
             permission='manage',
             route_name='abo_detail')
def abo_detail(request):
    '''
    show details about one contribution
    '''
    _id = request.matchdict['_id']
    _abo = Abo.get_by_id(_id)
    # check abo exists or redirect to dashboard
    if isinstance(_abo, NoneType):
        request.session.flash(
            'this abo id was not found in the DB',
            'messages'
        )
        return HTTPFound(location=request.route_url(
            'dash'))
    else:
        print Transfers.get_all_transfers_by_aboid(_abo.id)
        return {
            'abo': _abo,
            'transfers': Transfers.get_all_transfers_by_aboid(_abo.id),
        }


@view_config(permission='manage',
             route_name='payment_received')
def payment_received(request):
    """
    This view lets accountants update abo payment info
    has their payment arrived?
    """
    abo_id = request.matchdict['abo_id']
    dashboard_page = request.cookies['on_page']
    _abo = Abo.get_by_id(abo_id)

    if _abo.payment_received is True:  # change to NOT SET
        _abo.payment_received = False
        _abo.payment_received_date = datetime.datetime(1970, 1, 1)
    elif _abo.payment_received is False:  # set to NOW
        _abo.payment_received = True
        _abo.payment_received_date = datetime.datetime.now()
        if _abo.linkcode is None:
            print "linkcode did not exist before"
            _abo.linkcode = make_random_linkcode()
        else:
            pass
            #print "linkcode did exist: {}".format(_abo.linkcode)
        _transfer = Transfers(
            abo_id=_abo.id,
            date=datetime.datetime.now(),
            amount=_abo.amount,
        )
        DBSession.add(_transfer)

    log.info(
        "payment info of abo.id {} changed by {} to {}".format(
            _abo.id,
            request.user.login,
            _abo.payment_received
        )
    )
    return HTTPFound(
        request.route_url(
            'dash',
            #number=dashboard_page,
        )
    )


@view_config(route_name='send_confirmation_email',
             permission='manage')
def send_mail_view(request):
    """
    this view sends a mail to the user
    with links to her subscription badge image and page
    """
    _id = request.matchdict['abo_id']
    _abo = Abo.get_by_id(_id)
    if isinstance(_abo, NoneType):
        return HTTPFound(
            request.route_url(
                'dash',
                #number=request.cookies['on_page'],
                #order=request.cookies['order'],
                #orderby=request.cookies['orderby'],
                #'dashboard',
                #number=request.cookies['on_page'],
                #order=request.cookies['order'],
                #orderby=request.cookies['orderby'],
            )
        )
    _url = request.registry.settings['the_url']
    mailer = get_mailer(request)
    body_lines = mailbody_transfer_received(_abo, _url)
    #print '#'*80
    #print body_lines
    #print '*'*60
    the_mail_body = u''.join([line for line in body_lines])
    the_mail = Message(
        subject=_(u"C3S ZuschussAbo: deine Links!"),
        sender="noreply@c3s.cc",
        recipients=[_abo.email],
        body=the_mail_body
    )
    from smtplib import SMTPRecipientsRefused
    try:
        mailer.send(the_mail)
        #mailer.send_immediately(the_mail, fail_silently=False)
        #print(the_mail.body)
        _abo.payment_confirmed_email = True
        _abo.payment_confirmed_email_date = datetime.datetime.now()

    except SMTPRecipientsRefused:  # pragma: no cover
        print('SMTPRecipientsRefused')
        log.info('no connection/SMTPRecipientsRefused')
        return HTTPFound(
            request.route_url('dash', number=request.cookies['on_page'],))

    # 'else': send staffer to the dashboard
    return HTTPFound(request.route_url('dash',
                                       number=0  # request.cookies['on_page'],
                                       #order=request.cookies['order'],
                                       #orderby=request.cookies['orderby'],
                                       )
                     )


@view_config(permission='manage',
             route_name='delete_entry')
def delete_entry(request):
    """
    This view lets accountants delete entries (e.g. doublettes)
    """
    abo_id = request.matchdict['abo_id']
    _abo = Abo.get_by_id(abo_id)

    Abo.delete_by_id(_abo.id)
    log.info(
        "abo.id %s was deleted by %s" % (
            _abo.id,
            request.user.login,
        )
    )
    _message = "abo.id %s was deleted" % _abo.id

    request.session.flash(_message, 'messages')
    return HTTPFound(
        request.route_url('dash'))
