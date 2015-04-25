# -*- coding: utf-8 -*-
import datetime

from dentonpolice import jail


class TestMakeJailReportKeyName(object):

    def test_return_value(self):
        # Given a timestamp
        timestamp = datetime.datetime(2015, 4, 21, 17, 28, 20, 565745)
        # When we make a key-name from a timestamp
        result = jail._make_jail_report_key_name(timestamp=timestamp)
        # Then the value should be what we expect
        expected = 'jail_report/dentonpolice/2015/04/21/20150421172820.html'
        assert result == expected
