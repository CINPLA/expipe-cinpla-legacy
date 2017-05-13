import quantities as pq
from datetime import timedelta, datetime
import expipe.io
from distutils.util import strtobool
import sys

DTIME_FORMAT = expipe.io.core.datetime_format


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [[Y]/n] "
    elif default == "no":
        prompt = " [y/[N]] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def deltadate(adjustdate, regdate):
    delta = regdate - adjustdate if regdate > adjustdate else timedelta.max
    return delta


def register_depth(project, action, left=None, right=None):
    regdate = datetime.strptime(action.datetime, DTIME_FORMAT)
    if left is None or right is None:
        ratnr = action.id.split('-')[0]
        try:
            adjustments = project.get_action(name=ratnr + '-adjustment')
        except IOError as e:
            raise IOError(
                str(e) + ', depth parameters left and right must be given')
        adjusts = {}
        for adjust in adjustments.modules:
            values = adjust.to_dict()
            adjusts[datetime.strptime(values['date'], DTIME_FORMAT)] = adjust

        adjustdates = adjusts.keys()
        adjustdate = min(adjustdates, key=lambda x: deltadate(x, regdate))
        adjustment = adjusts[adjustdate].to_dict()
        adleft = adjustment['depth'][0]
        adright = adjustment['depth'][1]
        assert adjustment['location'].lower() == 'left, right'
    left = left or adleft
    right = right or adright
    answer = query_yes_no(
        'Are the following values correct:' +
        ' left = {}, right = {}, '. format(left, right) +
        'adjust date time = {}'.format(adjustdate))
    if answer == False:
        print('Aborting depth registration')
        return
    L = action.require_module('electrophysiology_L').to_dict()
    L['depth'] = pq.Quantity(left, 'mm')
    print('Registering depth left = ', L['depth'])
    action.require_module('electrophysiology_L', contents=L,
                          overwrite=True)
    R = action.require_module('electrophysiology_R').to_dict()
    R['depth'] = pq.Quantity(right, 'mm')
    print('Registering depth right = ', R['depth'])
    action.require_module('electrophysiology_R', contents=R,
                          overwrite=True)
