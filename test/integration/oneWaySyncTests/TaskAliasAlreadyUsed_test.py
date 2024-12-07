# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, missing-class-docstring
# pylint: disable=global-statement
import logging
import pickle
import pytest
from mockito import when, mock, unstub, when2, verify, captor, ANY, patch
import vcr
import requests

# test imports
# pylint: disable=import-error
from common_fixtures import empty_pickle, auth_cfg # pylint: disable=unused-import
from helpers import TestHelpers

from one_way_sync import sync_todoist_to_habitica
# pylint: enable=invalid-name

# initialization
HELPER = TestHelpers()
POST_COUNT = 0


def fake_post(url, data=None, json=None, **kwargs): # pylint: disable=unused-argument, redefined-outer-name
    errors_result = [{'message': 'Task alias already used on another task.',
                      'path': 'alias',
                      'value': data['alias']}]
    json_result = {'success': False,
                   'error': 'BadRequest',
                   'message': 'todo validation failed',
                   'errors': errors_result}

    # set default response
    response = mock({'status': 400, 'ok': False,
                     'status_code': '400'},
                    spec=requests.Response)

    when(response).json().thenReturn(json_result)
    global POST_COUNT
    POST_COUNT += 1
    return response


class TestTaskAliasAlreadyUsed:
    test_vcr = vcr.VCR(
        serializer='yaml',
        cassette_library_dir=TestHelpers.get_cassette_dir(),
        record_mode='once',
        match_on=['uri', 'method'],
        filter_headers=[('Authorization', 'Bearer d1347120363c2b310653f610d382729bd51e13c6'),
                        ('x-api-key', '18f22441-2c87-6d8e-fb2a-3fa670837b5a'),
                        ('x-api-user', 'cd18fc9f-b649-4384-932a-f3bda6fe8102'),
                        ('Cookie', "<redacted>")],
        before_record_request=HELPER.handle_request(),
        before_record_response=HELPER.scrub_response(debug=False),
        record_on_exception=False,
        decode_compressed_response=True
    )

    # pylint: disable=redefined-outer-name, unused-argument
    @pytest.mark.parametrize("pickle_in", [empty_pickle()], indirect=True)
    def test_task_alias_already_used(self,
                                     auth_cfg,
                                     pickle_in):
        # pylint: enable=redefined-outer-name, unused-argument
        ''' you need to initialize logging,
            otherwise you will not see anything from vcrpy '''
        logging.basicConfig()
        vcr_log = logging.getLogger("vcr")
        vcr_log.setLevel(logging.DEBUG)

        with self.test_vcr.use_cassette("test.yaml"):
            # patch post to habitica with fake
            patch(requests, 'post', replacement=fake_post)

            # mock read in of pickle file
            pkl_file = mock()
            pkl_load = mock()
            when2(open, 'oneWay_matchDict.pkl', 'rb').thenReturn(pkl_file)
            when(pickle).Unpickler(...).thenReturn(pkl_load)
            when(pkl_load).load().thenReturn({})

            # mock dump of pickle file
            pkl_out = mock()
            # when2(open, ...).thenCallOriginalImplementation()
            when2(open, 'oneWay_matchDict.pkl', 'wb').thenReturn(pkl_file)
            when(pickle).Pickler(...).thenReturn(pkl_out)
            when(pkl_out).dump(...)

            # execute
            sync_todoist_to_habitica()

            # verify pickle dump
            dump_dict = captor(ANY(dict))
            verify(pkl_out, times=1).dump(dump_dict)
            data = dump_dict.value
            assert len(data.keys()) == 63

            # check # of post to habitica
            assert POST_COUNT == 1

            # clean-up
            unstub()
