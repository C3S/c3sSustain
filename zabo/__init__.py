from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from sqlalchemy import engine_from_config

from .models import (
    #DBSession,
    Base,
)
from .security import (
    Root,
    groupfinder,
)
from .security.request import RequestWithUserAttribute


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    session_factory = session_factory_from_settings(settings)
    authn_policy = AuthTktAuthenticationPolicy(
        's0secret!!',
        callback=groupfinder,
    )
    authz_policy = ACLAuthorizationPolicy()
    #DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        session_factory=session_factory,
        root_factory=Root,
    )
    # mend request factory
    config.set_request_factory(RequestWithUserAttribute)
    # includes (other packages)
    config.include('pyramid_chameleon')  # templating
    config.include('pyramid_mailer')  # mailings
    # i18n stuff
    config.add_translation_dirs(
        'colander:locale/',
        'deform:locale/',  # copy deform.po and .mo to locale/de/LC_MESSAGES/
        'zabo:locale/')
    # static views
    config.add_static_view('static_deform', 'deform:static')
    config.add_static_view('static', 'static', cache_max_age=3600)
    # subscribers
    config.add_subscriber(
        'zabo.subscribers.add_base_bootstrap_template',
        'pyramid.events.BeforeRender')
    config.add_subscriber('zabo.subscribers.add_backend_template',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('zabo.subscribers.add_locale_to_cookie',
                          'pyramid.events.NewRequest')
    # routes
    config.add_route('home', '/')
    #svg
    config.add_route('wintervorrat', '/wintervorrat_{size}.{lang}.svg')
    #
    config.add_route('zform', '/now')
    config.add_route('confirm_data', '/confirm')
    config.add_route('sendmail', '/done')
    # admin/accounting
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('dash', '/dash')
    config.add_route('dashboard', '/dashboard/{number}/{orderby}/{order}')
    config.add_route('autocomplete_refcode_input_values', '/ariv/')
    config.add_route('abo_detail', '/abo_detail/{_id}')
    config.add_route('abo_edit', '/abo_edit/{_id}')
    config.add_route('new_abo', '/new_abo')
    config.add_route('payment_received', '/paym_recd/{abo_id}')
    config.add_route('payment_received_again', '/paym_recd_again/{abo_id}')
    config.add_route('send_confirmation_email', '/mail_mail_conf/{abo_id}')
    config.add_route('delete_entry', '/del_entry/{abo_id}')
    # statistics
    config.add_route('stats', '/stats')
    # sponsor badge links
    config.add_route('sponsor_image_small', '/verify/{linkcode}_s.png')
    config.add_route('sponsor_image', '/verify/{linkcode}.png')
    config.add_route('sponsor_page', '/verify/{linkcode}.html')

    config.scan()
    return config.make_wsgi_app()
