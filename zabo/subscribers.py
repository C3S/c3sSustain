from pyramid.renderers import get_renderer


def add_base_bootstrap_template(event):
    base_bootstrap = get_renderer(
        'templates/base_bootstrap.pt').implementation()
    event.update({'base_bootstrap': base_bootstrap})


def add_backend_template(event):
    backend = get_renderer('templates/backend.pt').implementation()
    event.update({'backend': backend})
