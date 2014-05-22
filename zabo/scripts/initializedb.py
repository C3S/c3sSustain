import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from ..models import (
    DBSession,
    Staff,
    Group,
    Abo,
    Base,
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        staff_group = Group(name=u"staff")
        DBSession.add(staff_group)
        rut = Staff(
            login=u'rut',
            password=u'berries',)
        rut.groups = [staff_group]
        DBSession.add(rut)
        first_abo = Abo(
            name=u'test',
            email=u'test@shri.de',
            amount=42,
        )
        first_abo.locale = 'de'
        DBSession.add(first_abo)
        second_abo = Abo(
            name=u'test2',
            email=u'test2@shri.de',
            amount=23,
        )
        second_abo.locale = 'en'
        DBSession.add(second_abo)
