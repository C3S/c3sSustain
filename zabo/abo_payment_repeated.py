from datetime import datetime
import logging
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from types import NoneType

from zabo.models import (
    Abo,
    DBSession,
    Transfers,
)

log = logging.getLogger(__name__)


@view_config(permission='manage',
             route_name='payment_received_again')
def payment_received_again(request):
    """
    This view lets accountants update abo payment info
    has their payment arrived?
    """
    abo_id = request.matchdict['abo_id']
    dashboard_page = request.cookies['on_page']
    _abo = Abo.get_by_id(abo_id)
    _referer = request.headers.get('Referer')

    print _referer

    if isinstance(_abo, NoneType):
        return HTTPFound(request.route_url('dash'))
    #print '#'*80
    #print request.POST
    #print '#'*80

    # TODO: set date of last payment
    if 'repayment_date' in request.POST:
        try:
            _repayment_date = datetime.strptime(
                request.POST['repayment_date'], '%Y-%m-%d')
        except ValueError, ve:
            request.session.flash('wrong date? {}'.format(ve.message))
            return HTTPFound(request.route_url('dash'))
    else:
        return HTTPFound(request.route_url('dash'))

    _abo.payment_last_date = _repayment_date
    _transfer = Transfers(
        abo_id=_abo.id,
        date=_repayment_date,
        amount=_abo.amount,
    )
    DBSession.add(_transfer)

    log.info(
        "repeated payment info of abo.id {} reported by {}".format(
            _abo.id,
            request.user.login,
        )
    )

    # redirect either to dashboard or to details page,
    # depending on where this came from
    if (
            not isinstance(_referer, NoneType)
    ) and 'dash' in _referer:  # pragma: no cover
        return HTTPFound(
            request.route_url(
                'dash',
                number=dashboard_page,
            )
        )
    else:  # assume we came from the datails page
        return HTTPFound(
            request.route_url(
                'abo_detail',
                _id=_abo.id,
            )
        )
