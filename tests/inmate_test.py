# -*- coding: utf-8 -*-
import mock
import pytest

from dentonpolice import inmate


class TestInmate(object):

    @pytest.fixture
    def inmate(self):
        return inmate.Inmate(
            id=134,
            name='SMITH, JOHN',
            DOB='1901/01/01',
            arrest='2015/04/19 22:41:40',
            seen='2015-04-19 22:42:13.123456',
            charges=[
                {
                    'amount': '$500.00',
                    'charge': 'FOO BAR BAZ',
                    'type': 'BOND',
                }
            ],
        )

    def test_smoke(self, inmate):
        assert inmate.first_name == 'John'

    def test_sort_by_arrest(self):
        # Given a list of inmates not sorted by arrest time
        first = mock.Mock(spec_set=['arrest'], arrest='04/30/2015 06:24:32')
        middle = mock.Mock(spec_set=['arrest'], arrest='04/30/2015 12:01:08')
        last = mock.Mock(spec_set=['arrest'], arrest='04/30/2015 15:07:14')
        inmate_list = [last, first, middle]
        # When we sort the list by arrest date
        sorted_list = sorted(
            inmate_list,
            key=inmate.Inmate.sort_key_for_arrest,
        )
        # Then the list should be sorted by arrest date.
        assert sorted_list == [first, middle, last]
