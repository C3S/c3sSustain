# _*_ coding: utf-8 -*-
import colander
from colander import Range
import deform
from deform import ValidationFailure
#from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
#from sqlalchemy.exc import DBAPIError

from pkg_resources import resource_filename
from translationstring import TranslationStringFactory

deform_templates = resource_filename('deform', 'templates')
zabo_templates = resource_filename('zabo', 'templates')

my_search_path = (deform_templates, zabo_templates)

_ = TranslationStringFactory('zabo')

from .models import (
    DBSession,
    Abo,
)


@view_config(route_name='zform', renderer='templates/zform.pt')
def zform_view(request):
    '''
    the main form
    '''
    class AboForm(colander.MappingSchema):
        name = colander.SchemaNode(
            colander.String(),
            title='Name oder Alias',
        )
        email = colander.SchemaNode(
            colander.String(),
            title='Email',
            validator=colander.Email(),
        )
        amount = colander.SchemaNode(
            colander.Integer(),
            #widget=deform.widget.MoneyInputWidget(
            #    options={'allowZero': False}),
            title='Betrag (in ganzen €)',
            validator=Range(
                min=5,
                min_err=_(u'mindestens 5 Euro, '
                          u'sonst sind die anfallenden Gebühren zu hoch.'),
            )
        )
    schema = AboForm()

    zform = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', 'Eingaben prüfen')
        ]
    )

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
                (u"Please note: There were errors, "
                 "please check the form below."),
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


@view_config(route_name='confirm_data', renderer='templates/confirm_data.pt')
def confirm_abo(request):
    '''
    show the data received to the user and let her confirm the submission
    '''
    #print request.POST
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
                title='Name oder Alias',
                widget=deform.widget.TextInputWidget(readonly=True),
            )
            email = colander.SchemaNode(
                colander.String(),
                title='Email',
                validator=colander.Email(),
                widget=deform.widget.TextInputWidget(readonly=True),
            )
            amount = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.MoneyInputWidget(
                    options={'allowZero': False},
                    readonly=True,),
                title='Betrag',
            )
        schema = AboForm()

        confirmform = deform.Form(
            schema,
            buttons=[
                deform.Button('sendmail', 'Eingaben bestätigen'),
                deform.Button('re-edit', 'Eingaben verändern'),
            ]
        )

        return {'confirmform': confirmform.render(
                appstruct=appstruct)}

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
        DBSession.add(new_abo)
        DBSession.flush()

        #print "added Abo #{}: {}".format(new_abo.id, new_abo.refcode)
        # send email
        mailer = get_mailer(request)
        body_lines = (  # a list of lines
            u'Hallo ', new_abo.name, u''' !

Wir haben Deine Abonnementsdaten erhalten.

Bitte richte nun einen monatlichen Dauerauftrag ein über ''',
            str(new_abo.amount) + u''' Euro
auf unser Konto bei der

EthikBank eG
Kontoinhaber: C3S SCE
BIC:\t GENO DE F1 ETK
IBAN:\t DE79830944950003264378

Betrag (€): ''' + str(new_abo.amount) + u'''
Verwendungszweck: ''' + new_abo.refcode + u'''

Bitte achte auf den Verwendungszweck, damit wir die Zahlung zweifelsfrei
Dir zuordnen können.

Sobald wir den Eingang der Zahlung bemerken, schicken wir Dir eine Email mit
Links zu deiner Grafik und der Bestätigungsseite, die dein Engagement zeigt.
''',
            (u"Bis bald!"), u'''

''',
            (u"Dein C3S-Team"),
        )
        the_mail_body = ''.join([line for line in body_lines])
        the_mail = Message(
            subject=(u"C3S Zuschuss Abo: bitte überweisen!"),
            sender="noreply@c3s.cc",
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
            subject='[C3S_ZA] neues abo?',
            sender="noreply@c3s.cc",
            recipients=[
                request.registry.settings['mailrecipient']],
            body=encrypt_with_gnupg(u'''
we just send email to a user:
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
        }
    # 'else': send user to the form
    return HTTPFound(location=request.route_url('zform'))
