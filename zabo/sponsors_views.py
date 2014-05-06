import os
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from types import NoneType

from .models import Abo


@view_config(renderer='templates/sponsor.pt',
             route_name='sponsor_page')
def sponsor_view(request):
    """
    show a page confirming the sponsors payment
    """
    #print "this is sponsor view"
    _code = request.matchdict['linkcode']
    _abo = Abo.get_by_linkcode(_code)
    if isinstance(_abo, NoneType):
        print "=== not found in DB"
        request.session.flash('this linkcode is invalid', 'messages')
        return {
            'invalid': True,
            'message': "this linkcode is invalid.",
            'abo': None
        }
    return {
        'invalid': False,
        'message': '',
        'abo': _abo
    }


@view_config(route_name='sponsor_image')
def sponsor_image(request):
    """
    return an image depending on the amount given
    (see get_sponsorshipGrade)
    """
    #print "this is sponsor image"
    _code = request.matchdict['linkcode']
    _abo = Abo.get_by_linkcode(_code)
    if isinstance(_abo, NoneType):
        the_url = 'zabo:static/badge_invalid.png'
        return HTTPFound(request.static_url(the_url))
    #the_url = 'zabo:static/badge' + _abo.get_sponsorshipGrade() + '.png'
    #return HTTPFound(request.static_url(the_url))
    # XXX TODO: spool the files, don't serve from static !!!
    # link must be unknown to outside!
    the_file = os.path.abspath(
        os.path.join(
            'zabo/static_offline/badge' + _abo.get_sponsorshipGrade() + '.png')
    )
    response = Response(content_type='image/png')
    response.app_iter = open(the_file, "r")
    return response  # pragma: no cover
