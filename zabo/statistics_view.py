from pyramid.view import view_config

from .models import Abo


@view_config(renderer='templates/stats.pt',
             permission='manage',
             route_name='stats')
def stats_view(request):
    """


    This view lets accountants view statistics:
    how many subscriptions of which category, payment status, etc.
    """
    #print("who is it? %s" % request.user.login)
    return {
        '_number_of_datasets': Abo.get_number(),
        'sum_abos_total': Abo.get_sum_abos_total(),
        'sum_abos_unpaid': Abo.get_sum_abos_unpaid(),
        'sum_abos_paid': Abo.get_sum_abos_paid(),
    }
