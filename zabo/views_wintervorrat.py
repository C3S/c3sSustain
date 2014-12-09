# -*- coding: utf-8 -*-

from pyramid.view import view_config
#from pyramid.request import Request
#import envoy
from .models import Abo


## png
#@view_config(route_name='wintervorrat_S_png')
#             renderer='templates/wintervorrat.pt'
#def wintervorrat_small_png(request):
#    '''
#    wintervorrat png small
#    '''
#    request.response.content_type = 'image/png'
#    req = Request.blank('/wintervorrat_l.svg')
#    svg = req.invoke_subrequest(req)
#    #svg_file =
#    #p = envoy.run('convert ')
#    print svg


## svg
@view_config(route_name='wintervorrat',
             renderer='templates/wintervorrat.pt')
def wintervorrat_view(request):
    '''
    wintervorrat svg: show progress of aktion wintervorrat
    three sizes: s, m, l,
    two languages: de + en
    '''
    request.response.content_type = 'image/svg+xml'
    # get language and size from matchdict
    _lang = request.matchdict['lang']
    _size = request.matchdict['size']
    # prefetch values from DB
    _paid = Abo.get_sum_abos_paid()
    _unpaid = Abo.get_sum_abos_unpaid()
    _num_unpaid = Abo.get_num_abos_unpaid()
    _num_paid = Abo.get_num_abos_paid()
    _target_amount = 3700
    # text depending on language
    if _lang == 'de':
        _link_to_blog = 'https://www.c3s.cc/wintervorrat/'
        _running_costs = (
            u"Die laufenden Kosten der C3S betragen €{} "
            u"im Monat.".format(_target_amount))
        _unpaid_subscriptions = (
            u"Es gibt aktuell {} Neuanmeldungen, die uns Zuwendungen von "
            u"insgesamt €{} im Monat in Aussicht stellen.").format(
                _num_unpaid, _unpaid)
        _paid_subscriptions = (
            u"Wir haben {} aktive Sustainer, die im Monat "
            u"€{} zusammentragen!").format(
                _num_paid, _paid)
        _text_preposition = u"von"
    else:
        _link_to_blog = 'https://www.c3s.cc/en/winter-stock/'
        _running_costs = (
            u"Running costs of the C3S sum up to €{} "
            u"per month.".format(_target_amount))
        _unpaid_subscriptions = (
            u"Currently, there are {} new subscriptions, holding out the "
            u"prospect of €{} per month.").format(
                _num_unpaid, _unpaid)
        _paid_subscriptions = (
            u"We have {} active 'Sustainers', raising €{} in total "
            u"each month!").format(
                _num_paid, _paid)
        _text_preposition = u"of"
    # settings depending on size
    if _size == 'l':
        """
        large font
        """
        _image_height = 400
        _font_size = 270
        if 3000 >= _paid > 2500:
            _font_size_target = 200
        elif _paid > 3000:
            _font_size_target = 120
        else:
            _font_size_target = 270
        _text_x = (_paid - 20) if _paid < 2500 else 2500
        _text_y = 300
    elif _size == 'm':
        """
        medium font
        """
        _image_height = 200
        _font_size = 180
        if 3000 >= _paid > 2900:
            _font_size_target = 135
        elif _paid > 3000:
            _font_size_target = 90
        else:
            _font_size_target = 180
        _text_x = (_paid - 20) if _paid < 2900 else 2900
        _text_y = 170
    elif _size == 's':
        """
        small font
        """
        _image_height = 100
        _font_size = 100
        if 3400 >= _paid > 3200:
            _font_size_target = 60
        elif _paid > 3400:
            _font_size_target = 40
        else:
            _font_size_target = 100
        _text_x = (_paid - 20) if _paid < 3200 else 3200
        _text_y = 85
    return {
        'link_to_blog': _link_to_blog,
        'target_amount': _target_amount,
        'sum_sustain_total': Abo.get_sum_abos_total(),
        'sum_sustain_unpaid': _unpaid,
        'sum_sustain_paid': _paid,
        'num_sustain_unpaid': _num_unpaid,
        'num_sustain_paid': _num_paid,
        # text specific to language
        'text_running_costs': _running_costs,
        'text_paid_subscriptions': _paid_subscriptions,
        'text_unpaid_subscriptions': _unpaid_subscriptions,
        'text_preposition': _text_preposition,
        # values specific to size
        'image_height': _image_height,
        'text_x': _text_x,
        'text_y': _text_y,
        'font_size': _font_size,
        'font_size_target': _font_size_target,
    }
