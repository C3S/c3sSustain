import os
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_locale_name
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
    if 'de' in get_locale_name(request):
        financial_blog_url = request.registry.settings['financial_blog_url_de']
    else:
        financial_blog_url = request.registry.settings['financial_blog_url_en']
    if isinstance(_abo, NoneType):
        #print "=== not found in DB"
        request.session.flash('this linkcode is invalid', 'messages')
        return {
            'financial_situation_blog': financial_blog_url,
            'invalid': True,
            'message': "this linkcode is invalid.",
            'abo': None
        }
    return {
        'financial_situation_blog': financial_blog_url,
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
        if request.locale_name == 'de':
            the_url = 'zabo:static/ungueltig.png'
        else:
            the_url = 'zabo:static/invalid.png'
        return HTTPFound(request.static_url(the_url))
    #the_url = 'zabo:static/badge' + _abo.get_sponsorshipGrade() + '.png'
    #return HTTPFound(request.static_url(the_url))
    # XXX TODO: spool the files, don't serve from static !!!
    # link must be unknown to outside!
    base_path = request.registry.settings['base_path'] or ''
    the_file = os.path.abspath(
        os.path.join(
            base_path,
            'zabo/static_offline/badge' + _abo.get_sponsorshipGrade() + '.png')
    )
    response = Response(content_type='image/png')
    response.app_iter = open(the_file, "r")
    return response  # pragma: no cover


@view_config(route_name='sponsor_image_small')
def sponsor_image_small(request):
    """
    return a smaller image depending on the amount given
    (see get_sponsorshipGrade)
    """
    #print "this is sponsor image"
    _code = request.matchdict['linkcode']
    _abo = Abo.get_by_linkcode(_code)
    if isinstance(_abo, NoneType):
        if request.locale_name == 'de':
            the_url = 'zabo:static/ungueltig_s.png'
        else:
            the_url = 'zabo:static/invalid_s.png'
        return HTTPFound(request.static_url(the_url))
    #the_url = 'zabo:static/badge' + _abo.get_sponsorshipGrade() + '.png'
    #return HTTPFound(request.static_url(the_url))
    # XXX TODO: spool the files, don't serve from static !!!
    # link must be unknown to outside!
    base_path = request.registry.settings['base_path'] or ''
    the_file = os.path.abspath(
        os.path.join(
            base_path,
            'zabo/static_offline/badge' + _abo.get_sponsorshipGrade() + '_s.png')
    )
    response = Response(content_type='image/png')
    response.app_iter = open(the_file, "r")
    return response  # pragma: no cover
