# -*- coding: utf-8 -*-
from dentonpolice import inmate


class TestInmate(object):

    def test_smoke(self):
        # TODO(bwbaugh#GH-9|2015-04-19): Replace with real tests.
        inmate.Inmate(
            id=134,
            name='John Smith',
            DOB='1901/01/01',
            arrest='2015-04-19 22:41:40',
            seen='2015-04-19 22:42:13',
            charges=[
                {
                    'amount': '$500.00',
                    'charge': 'FOO BAR BAZ',
                    'type': 'BOND',
                }
            ],
        )
