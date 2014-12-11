import colander
from colander import Range
import deform
from deform import ValidationFailure

from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import view_config

from types import NoneType

from zabo.models import (
    Abo,
    Transfers
)
from zabo.views import (
    _,
    zpt_renderer,
)
import logging
log = logging.getLogger(__name__)


@view_config(renderer='templates/abo_edit.pt',
             permission='manage',
             route_name='abo_edit')
def abo_edit(request):
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
                        u'at least 5 Euro, or the cost of transfer '
                        u'is too high.'),
                )
            )
        schema = AboForm()

        zform = deform.Form(
            schema,
            buttons=[
                deform.Button('submit', _(u'Verspeichern')),
            ],
            renderer=zpt_renderer,
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
                    _(u"Please note: There were errors, "
                      u"please check the form below."),
                    'message_above_form',
                    allow_duplicate=False)
                return{
                    'zform': e.render(),
                    'abo': _abo,
                    'transfers': Transfers.get_all_transfers_by_aboid(_abo.id),
                }

            # validation worked. now do something
            # store information in the database
            # check if values are correct
            listing = [
                ('name', appstruct['name']),
                ('email', appstruct['email']),
                ('amount', appstruct['amount']),
            ]
            for thing in listing:

                v = thing[0]

                if _abo.__getattribute__(v) == thing[1]:
                    #print "no change for %s" % thing[0]
                    pass
                else:
                    #print ("change in %s:" % thing[0])
                    log.info(  # XXX this needs to go into the logs
                        "%s changes %s of id %s to %s" % (
                            authenticated_userid(request),
                            thing[0],
                            _abo.id,
                            thing[1]
                        )
                    )
                    setattr(_abo, v, thing[1])

            return HTTPFound(request.route_url('abo_detail', _id=_abo.id))
        else:  # not submit in request.POST
            pass
            #print request.POST
            #if 'appstruct' in request.session:
            #    #print request.session['appstruct']
            #    appstruct = request.session['appstruct']
            #    # delete info from session
            #    #request.session['appstruct'] = dict()
            #    del request.session['appstruct']
            #    return {'zform': zform.render(appstruct)}

        #print Transfers.get_all_transfers_by_aboid(_abo.id)

        # prepare appstruct for pre-filling of form
        appstruct = {}
        appstruct['name'] = _abo.name
        appstruct['email'] = _abo.email
        appstruct['amount'] = _abo.amount

        # pre-fill the form with values from the DB
        zform.set_appstruct(appstruct)

        return {
            'zform': zform.render(),
            'abo': _abo,
            'transfers': Transfers.get_all_transfers_by_aboid(_abo.id),
        }
