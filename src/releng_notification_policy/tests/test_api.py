import pytest
from releng_notification_policy.api import create_identity_preference_url, determine_message_action, get_identity_url_for_actionable_policies
from releng_notification_policy.models import Policy, Message
from datetime import datetime, timedelta
from operator import itemgetter


@pytest.fixture
def list_of_messages():
    common = {
        'message': 'dummy message text',
        'shortMessage': 'test',
    }

    datetime_today = datetime.today()
    hour = timedelta(hours=1)

    test_configs = [
        {
            'uid': 'pass1',
            'deadline': datetime_today - hour,
        },
        {
            'uid': 'fail1',
            'deadline': datetime_today + hour,
        },
    ]

    return [
        Message(**{**common, **config})
        for config in test_configs
    ]


@pytest.fixture
def list_of_policies():
    common = {
        'identity': 'dummy',
        'urgency': 'LOW',
        'message_id': 12345,
    }

    datetime_today = datetime.today()
    year = timedelta(days=365)
    hour = timedelta(hours=1)

    test_configs = [
        # Policy should be returned (first notification), between start/end timestamps
        {
            'id': 0,
            'start_timestamp': datetime_today - year,
            'stop_timestamp': datetime_today + year,
            'last_notified': None,
            'frequency': timedelta(minutes=1),
        },

        # Policy with future start/end times
        {
            'id': 1,
            'start_timestamp': datetime_today + 2 * year,
            'stop_timestamp': datetime_today + 3 * year,
            'last_notified': None,
            'frequency': timedelta(minutes=1),
        },

        # Policy with past start/end times
        {
            'id': 2,
            'start_timestamp': (datetime_today - 3 * year),
            'stop_timestamp': (datetime_today - 2 * year),
            'last_notified': None,
            'frequency': timedelta(minutes=1),
        },

        # Policy with valid times, invalid frequency
        {
            'id': 3,
            'start_timestamp': (datetime_today - year),
            'stop_timestamp': (datetime_today + year),
            'last_notified': (datetime_today - hour),
            'frequency': timedelta(hours=10),
        },

        # Policy with valid times, valid frequency, already notified
        {
            'id': 4,
            'start_timestamp': (datetime_today - year),
            'stop_timestamp': (datetime_today + year),
            'last_notified': (datetime_today - hour),
            'frequency': timedelta(minutes=1),
        },
    ]

    return [
        Policy(**{**common, **policy_config})
        for policy_config in test_configs
    ]


def test_get_identity_url_for_actionable_policies(app, list_of_policies):
    result = get_identity_url_for_actionable_policies(list_of_policies)
    results_only_policies = map(itemgetter(0), result)
    results_string_reprs = list(map(str, results_only_policies))
    assert all(val in results_string_reprs for val in [
        'Policy(id=0, message_uid=12345, identity=dummy, urgency=LOW)',
        'Policy(id=4, message_uid=12345, identity=dummy, urgency=LOW)',

    ]), 'An actionable policy did not register as actionable.'

    assert not any(val in results_string_reprs for val in [
        'Policy(id=1, message_uid=12345, identity=dummy, urgency=LOW)',
        'Policy(id=2, message_uid=12345, identity=dummy, urgency=LOW)',
        'Policy(id=3, message_uid=12345, identity=dummy, urgency=LOW)',

    ]), 'An unactionable policy registered as actionable.'


def test_create_identity_preference_url(app, list_of_policies):
    expected_result = 'https://fake_endpoint.mozilla-releng.net/identity/dummy/LOW'
    urls = list(map(create_identity_preference_url, list_of_policies))
    assert all(url == expected_result for url in urls), \
        'create_identity_preference_url does not always create the correct url.'


def test_determine_message_action(app, list_of_messages):
    result = list(determine_message_action(list_of_messages))
    bool_vals = list(map(itemgetter(1), result))
    assert bool_vals == [True, False], 'Determine message action did not correctly identify notifiable messages.'
