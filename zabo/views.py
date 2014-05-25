# _*_ coding: utf-8 -*-
import colander
from colander import Range
import deform
from deform import ValidationFailure
#from pyramid.response import Response
from pyramid.i18n import (
    get_locale_name,
    get_localizer,
)
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.threadlocal import get_current_request

#from sqlalchemy.exc import DBAPIError

from pkg_resources import resource_filename
from translationstring import TranslationStringFactory

deform_templates = resource_filename('deform', 'templates')
zabo_templates = resource_filename('zabo', 'templates')

my_search_path = (deform_templates, zabo_templates)

_ = TranslationStringFactory('zabo')


def translator(term):
    #print("=== this is def translator")
    return get_localizer(get_current_request()).translate(term)

my_template_dir = resource_filename('zabo', 'templates/')
deform_template_dir = resource_filename('deform', 'templates/')

zpt_renderer = deform.ZPTRendererFactory(
    [
        my_template_dir,
        deform_template_dir,
    ],
    translator=translator,
)
# the zpt_renderer above is referred to within the demo.ini file by dotted name

from .models import (
    DBSession,
    Abo,
)


@view_config(route_name='home', renderer='templates/landing_page.pt')
def landing_page_view(request):
    '''
    the landing page

    what people see when they hit the subdomain.

    all text is contained in the template: templates/landing_page.pt
    '''
    # if another language was chosen by clicking on a flag
    # the add_locale_to_cookie subscriber has planted an attr on the request
    if hasattr(request, '_REDIRECT_'):
        #print("request._REDIRECT_: " + str(request._REDIRECT_))

        _query = request._REDIRECT_
        #print("_query: " + _query)
        # set language cookie
        request.response.set_cookie('_LOCALE_', _query)
        request._LOCALE_ = _query
        #locale_name = _query
        #print("locale_name (from query_string): " + locale_name)
        #from pyramid.httpexceptions import HTTPFound
        #print("XXXXXXXXXXXXXXX ==> REDIRECTING ")
        return HTTPFound(location=request.route_url('home'),
                         headers=request.response.headers)
    else:
        locale_name = get_locale_name(request)

    financial_blog_url = request.registry.settings['financial_blog_url']
    # debug: check locale
    #print "the locale: {}".format(get_locale_name(request))

    return {
        'foo': 'bar',
        'financial_situation_blog': financial_blog_url,
    }


@view_config(route_name='zform', renderer='templates/zform.pt')
def zform_view(request):
    '''
    the main form
    '''
    class AboForm(colander.MappingSchema):
        name = colander.SchemaNode(
            colander.String(),
            title=_(u'Name or pseudonym'),
        )
        email = colander.SchemaNode(
            colander.String(),
            title=_(u'E-mail'),
            validator=colander.Email(),
        )
        amount = colander.SchemaNode(
            colander.Integer(),
            #widget=deform.widget.MoneyInputWidget(
            #    options={'allowZero': False}),
            title=_(u'Amount (in full Euro)'),
            validator=Range(
                min=5,
                max=10000,
                min_err=_(
                    u'at least 5 Euro, or the cost of transfer is too high.'),
            )
        )
    schema = AboForm()

    zform = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Check details')),
            deform.Button('why', _(u'Back')),
        ],
        renderer=zpt_renderer,
    )
    # if people want to know "Why sustain C3S", send them to the landing page
    if 'why' in request.POST:
        return HTTPFound(request.route_url('home'))
    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        #print "we got {}".format(request.POST.items())
        try:
            appstruct = zform.validate(controls)
            #print("the appstruct from the form: %s \n") % appstruct
            #for thing in appstruct:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)

        except ValidationFailure, e:
            #print("the appstruct from the form: %s \n") % appstruct
            #for thing in appstruct:
            #    print("the thing: %s") % thing
            #    print("type: %s") % type(thing)
            print(e)
            #message.append(
            request.session.flash(
                _(u"Please note: There were errors, "
                  u"please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{'zform': e.render()}

        # validation worked. now do something
        # store information in the session
        request.session['appstruct'] = appstruct
        return HTTPFound(request.route_url('confirm_data'))
    else:  # not submit in request.POST
        #print request.POST
        if 'appstruct' in request.session:
            #print request.session['appstruct']
            appstruct = request.session['appstruct']
            # delete info from session
            #request.session['appstruct'] = dict()
            del request.session['appstruct']
            return {'zform': zform.render(appstruct)}

    return {
        'zform': zform.render(),
    }


@view_config(route_name='confirm_data',
             renderer='templates/confirm_data.pt')
def confirm_abo(request):
    '''
    show the data received to the user and let her confirm the submission
    '''
    if 're-edit' in request.POST:
        #print "re-edit: go to form"
        return HTTPFound(location=request.route_url('zform'))
    if 'sendmail' in request.POST:
        return HTTPFound(location=request.route_url('sendmail'))

    #check if user has used the form or 'guessed' this URL
    if ('appstruct' in request.session):
        # we do have valid info from the form in the session
        appstruct = request.session['appstruct']
        # delete old messages from the session (from invalid form input)
        request.session.pop_flash('message_above_form')
        #print("show_success: locale: %s") % appstruct['_LOCALE_']

        class AboForm(colander.MappingSchema):
            name = colander.SchemaNode(
                colander.String(),
                title=_(u'Name or pseudonym'),
                widget=deform.widget.TextInputWidget(readonly=True),
            )
            email = colander.SchemaNode(
                colander.String(),
                title=_(u'Email'),
                validator=colander.Email(),
                widget=deform.widget.TextInputWidget(readonly=True),
            )
            amount = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.MoneyInputWidget(
                    options={'allowZero': False},
                    readonly=True,),
                title=_(u'Amount'),
            )
        schema = AboForm()

        confirmform = deform.Form(
            schema,
            buttons=[
                deform.Button('sendmail', _(u'Confirm Details')),
                deform.Button('re-edit', _(u'Change Details')),
            ],
            renderer=zpt_renderer,
        )
        #print "the amount: {}".format(appstruct['amount'])
        from .models import sponsorshipGrade
        grade = sponsorshipGrade(appstruct['amount'])
        banner_string = 'zabo:static/sustain/Stufe' + grade + '.jpg'
        banner_url = request.static_url(banner_string)

        return {
            'confirmform': confirmform.render(
                appstruct=appstruct),
            'banner_url': banner_url,
        }

    # 'else': send user to the form
    return HTTPFound(location=request.route_url('zform'))


@view_config(route_name='sendmail', renderer='templates/sendmail.pt')
def sendmail_view(request):
    """
    this view sends a mail to the user and tells her to transfer money
    """
    if 'appstruct' in request.session:
        appstruct = request.session['appstruct']

        # save info in DB
        #   rather do it here than over in the confirm_view
        #   because the information is still subject to change there,
        #   so we get duplicates

        new_abo = Abo(
            name=appstruct['name'],
            email=appstruct['email'],
            amount=str(appstruct['amount']),
        )
        new_abo.locale = get_locale_name(request)
        #print "the locale: {}".format(new_abo.locale)
        DBSession.add(new_abo)
        DBSession.flush()

        #print "added Abo #{}: {}".format(new_abo.id, new_abo.refcode)
        # send email
        mailer = get_mailer(request)

        from mail_utils import mailbody_transfer_directions
        the_mail_body = mailbody_transfer_directions(new_abo)

        the_mail = Message(
            subject=_(u'I sustain C3S: awaiting your contribution'),
            #(u"C3S Zuschuss Abo: bitte überweisen!"),
            sender=request.registry.settings['mail_from'],
            recipients=[new_abo.email, ],
            body=the_mail_body
        )
        try:
            mailer.send(the_mail)
            #print(the_mail.body)
        except:  # pragma: no cover
            print "mail NOT sent to {}!!!".format(new_abo.email)
            #print(the_mail.body)
        from zabo.gnupg_encrypt import encrypt_with_gnupg
        #print request.registry.settings
        # send mail to accountants
        acc_mail = Message(
            subject=_(u'[SUSTAIN] neu'),
            sender=request.registry.settings['mail_from'],
            recipients=[
                request.registry.settings['mailrecipient']],
            body=encrypt_with_gnupg(u'''
we just send email with payment information to a user:
name: %s
email: %s
amount: %s
''' % (appstruct['name'],
       appstruct['email'],
       str(appstruct['amount']))))
        mailer.send(acc_mail)
        # make the session go away
        request.session.invalidate()
        return {
            'firstname': appstruct['name'],
            'sender': request.registry.settings['mail_from'],
        }
    # 'else': send user to the form
    return HTTPFound(location=request.route_url('zform'))
