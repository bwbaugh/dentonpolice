# -*- coding: utf-8 -*-
import os

import mock
import pytest
import staticconf.testing

from dentonpolice import report_downloader


class TestShouldThrottle(object):

    @pytest.fixture
    def app_config(self, request):
        mock_config = {}
        mock_configuration = staticconf.testing.MockConfiguration(mock_config)
        mock_configuration.setup()
        request.addfinalizer(mock_configuration.teardown)
        return mock_configuration

    @pytest.fixture
    def mock_getmtime(self, request):
        patcher = mock.patch.object(os.path, 'getmtime', autospec=True)
        mock_instance = patcher.start()
        request.addfinalizer(patcher.stop)
        return mock_instance

    @pytest.mark.parametrize(
        argnames='last_report_time,at_time,min_report_age,should_throttle',
        argvalues=[
            (1, 5, 5, True),
            (1, 6, 5, False),
            (1, 7, 5, False),
        ],
    )
    def test_throttle_if_last_report_old_enough(
            self, last_report_time, at_time, min_report_age, should_throttle,
            app_config, mock_getmtime):
        # Given time to check for throttling is "<at_time>
        # And the last report was generated at "<last_report_time>"
        mock_getmtime.return_value = last_report_time
        # And the config requires "<min_report_age>" seconds to have passed
        app_config.namespace.update_values(
            {'minimum_report_age_s': min_report_age},
        )
        # When we check if we should throttle due to the last report time
        result = report_downloader._should_throttle(at_time=at_time)
        # Then the result should be "<should_throttle>"
        assert result is should_throttle

    def test_never_throttle_if_no_last_report(self, app_config, mock_getmtime):
        # Given the program has never generated a report before
        mock_getmtime.side_effect = OSError
        app_config.namespace.update_values({'minimum_report_age_s': 0})
        # When we check if we should throttle due to the last report time
        result = report_downloader._should_throttle(at_time=0)
        # Then we should not throttle
        assert result is False
