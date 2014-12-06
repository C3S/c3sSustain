from pyramid.view import view_config
from .models import Abo


@view_config(route_name='wintervorrat_S',
             renderer='templates/wintervorrat.pt')
def wintervorrat_small_view(request):
    '''
    wintervorrat svg small
    '''
    request.response.content_type = 'image/svg+xml'
    _paid = 3001  # Abo.get_sum_abos_paid()
    _unpaid = Abo.get_sum_abos_unpaid()
    if 3000 >= _paid > 2500:
        _font_size_target = 200
    elif _paid > 3000:
        _font_size_target = 120
    else:
        _font_size_target = 270
    _text_x = (_paid - 20) if _paid < 2500 else 2500
    return {
        'target_amount': 3700,
        'sum_sustain_total': Abo.get_sum_abos_total(),
        'sum_sustain_unpaid': _unpaid,
        'sum_sustain_paid': _paid,
        # values specific to size
        'image_height': 400,
        'text_x': _text_x,
        'text_y': 300,
        'font_size': 270,
        'font_size_target': _font_size_target,
    }


@view_config(route_name='wintervorrat_M',
             renderer='templates/wintervorrat.pt')
def wintervorrat_medium_view(request):
    '''
    wintervorrat svg
    '''
    _paid = Abo.get_sum_abos_paid()
    _unpaid = Abo.get_sum_abos_unpaid()
    request.response.content_type = 'image/svg+xml'
    if 3000 >= _paid > 2900:
        _font_size_target = 135
    elif _paid > 3000:
        _font_size_target = 90
    else:
        _font_size_target = 180
    _text_x = (_paid - 20) if _paid < 2900 else 2900
    return {
        'target_amount': 3700,
        'sum_sustain_total': Abo.get_sum_abos_total(),
        'sum_sustain_unpaid': _unpaid,
        'sum_sustain_paid': _paid,
        # values specific to size
        'image_height': 200,
        'text_x': _text_x,
        'text_y': 170,
        'font_size': 180,
        'font_size_target': _font_size_target,
    }


@view_config(route_name='wintervorrat_L',
             renderer='templates/wintervorrat.pt')
def wintervorrat_large_view(request):
    '''
    wintervorrat svg
    '''
    _paid = Abo.get_sum_abos_paid()
    _unpaid = Abo.get_sum_abos_unpaid()
    request.response.content_type = 'image/svg+xml'
    if 3400 >= _paid > 3200:
        _font_size_target = 60
    elif _paid > 3400:
        _font_size_target = 40
    else:
        _font_size_target = 100
    _text_x = (_paid - 20) if _paid < 3200 else 3200
    return {
        'target_amount': 3700,
        'sum_sustain_total': Abo.get_sum_abos_total(),
        'sum_sustain_unpaid': _unpaid,
        'sum_sustain_paid': _paid,
        # values specific to size
        'image_height': 100,
        'text_x': _text_x,
        'text_y': 85,
        'font_size': 100,
        'font_size_target': _font_size_target,
    }
