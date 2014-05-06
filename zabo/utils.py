import random
import string

from .models import Abo


def make_random_linkcode():
    """
    used as part of the link (URL) of sponsors page and image
    """
    randomstring = u''.join(
        random.choice(
            string.ascii_uppercase + string.digits
        ) for x in range(10))
    # check if code is already used
    print(
        "checking linkcode: %s" % Abo.check_for_existing_refcode(
            randomstring))
    while (Abo.check_for_existing_linkcode(randomstring)):
            # create a new one, if the new one already exists in the database
            #print("generating new code")
            randomstring = make_random_linkcode()  # pragma: no cover

    return randomstring
