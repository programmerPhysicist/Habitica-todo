# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, missing-class-docstring
# pylint: disable=global-statement
import os
import shutil
import logging
import json
import pickle
from urllib.parse import parse_qsl, urlencode
import requests

# test imports
# pylint: disable=import-error
import pytest
import vcr
from mockito import when, mock, unstub, when2, verify, captor, ANY, patch
from common_fixtures import empty_pickle
from one_way_sync import sync_todoist_to_habitica
# pylint: enable=invalid-name


class TestHelpers:
    def __init__(self):
        self.counter = 1
        self.resp_counter = 1
        self.uri = ""

    @staticmethod
    def get_root():
        pwd = os.getcwd()
        root = pwd.split("Project_Hype-Berry")[0]
        root = os.path.join(root, "Project_Hype-Berry")
        return root

    @staticmethod
    def get_cassette_dir():
        the_dir = os.path.join(TestHelpers.get_repo_path(), 'test/fixtures/cassettes')
        return the_dir

    @staticmethod
    def get_repo_path():
        if '__file__' in globals():
            self_name = globals()['__file__']
        elif '__file__' in locals():
            self_name = locals()['__file__']
        else:
            self_name = __name__
        file_path = self_name.split("Project_Hype-Berry")[0]
        root = os.path.join(file_path, "Project_Hype-Berry")
        return root

    def handle_request(self):
        def get_uri(request):
            self.uri = request.uri
            if request.method == "PUT":
                try:
                    body = json.loads(request.body)
                except ValueError:
                    body = bytes.decode(request.body)
                    query_dict = dict(parse_qsl(body))
                    query_dict['text'] = "some test task " + str(self.counter)
                    self.counter += 1
                    body = urlencode(query_dict)
                    request.body = body.encode()
                else:
                    body['text'] = "some test task " + str(self.counter)
                    self.counter += 1
                    request.body = json.dumps(body)
            return request
        return get_uri

    def scrub_habitica_resp(self, s_json):
        data = s_json['data']
        elem_num = len(data)
        for i in range(elem_num):
            if data[i]['type'] == 'habit':
                data[i]['text'] = "some test habit " + str(self.counter)
                if 'alias' in data[i].keys():
                    data[i]['alias'] = "sometesthabit" + str(self.counter)
            elif data[i]['type'] == 'todo' or data[i]['type'] == 'daily':
                data[i]['text'] = "some test task " + str(self.counter)
                if data[i]['checklist']:
                    cl_count = len(data[i]['checklist'])
                    for j in range(cl_count):
                        data[i]['checklist'][j]['text'] = "item " + str(j)
            elif data[i]['type'] == 'reward':
                data[i]['text'] = "some reward"
            else:
                print('Warning: Unknown type')
            if data[i]['notes'] != "":
                data[i]['notes'] = "Test notes"
            if data[i]['challenge']:
                data[i]['challenge']['shortName'] = "Test challenge"
            data[i]['userId'] = 'cd18fc9f-b649-4384-932a-f3bda6fe8102'
            self.counter += 1
        s_json['data'] = data
        notifications = s_json['notifications']
        num_nots = len(notifications)
        for i in range(num_nots):
            msg = notifications[i]
            if msg['type'] == 'GROUP_INVITE_ACCEPTED':
                body_text = msg['data']['bodyText']
                the_split = body_text.split(' accepted')
                username1 = the_split[0]
                body_text = body_text.replace(username1, "username1")
                the_str = the_split[1]
                the_str = the_str.split('to ')[1]
                username2 = the_str.split('\'s')[0]
                body_text = body_text.replace(username2, "username2")
                s_json['notifications'][i]['data']['bodyText'] = body_text
        return s_json

    def scrub_habitica_put_resp(self, s_json):
        s_json['data']['text'] = "some test task " + str(self.counter)
        s_json['data']['userId'] = "cd18fc9f-b649-4384-932a-f3bda6fe8102"
        return s_json

    def scrub_todoist_tasks(self, s_json):
        items = s_json
        num_items = len(items)
        for i in range(num_items):
            s_json[i]['content'] = "some test task " + str(self.counter)
            s_json[i]['description'] = "some test description"
            s_json[i]['user_id'] = "34534534534"
            self.counter += 1
        return s_json

    def scrub_todoist_completed(self, s_json):
        items = s_json['items']
        num_items = len(items)
        for i in range(num_items):
            s_json['items'][i]['content'] = "some test task " + str(self.counter)
            s_json['items'][i]['user_id'] = "34534534534"
            self.counter += 1
        for key in s_json['projects']:
            s_json['projects'][key]['name'] = "some test project " + str(self.counter)
            self.counter += 1
        for key in s_json['sections']:
            s_json['sections'][key]['user_id'] = "34534534534"
        return s_json

    def scrub_response(self, debug=False):
        def before_record_response(response):
            todoist_uri1 = "https://api.todoist.com/rest/v2/tasks"
            todoist_uri2 = "https://api.todoist.com/sync/v9/completed/get_all"
            habitica_uri1 = "https://habitica.com/api/v3/tasks/user/"
            habitica_uri2 = "https://habitica.com/api/v3/tasks"

            cookie = response['headers']['Set-Cookie']
            elem_num = len(cookie)
            for i in range(elem_num):
                response['headers']['Set-Cookie'][i] = "<redacted>"

            response['headers']['X-Amz-Cf-Id'] = "<redacted>"

            body = response['body']['string']
            s_json = json.loads(body)
            resp_type = ""
            if self.uri == habitica_uri1 and s_json['success']:
                s_json = self.scrub_habitica_resp(s_json)
                resp_type = "habitica_"
            elif habitica_uri2 in self.uri:
                s_json = self.scrub_habitica_put_resp(s_json)
                resp_type = "habitica_put_"
            elif self.uri == todoist_uri2:
                s_json = self.scrub_todoist_completed(s_json)
                resp_type = "todoist_completed_"
            elif self.uri == todoist_uri1:
                s_json = self.scrub_todoist_tasks(s_json)
                resp_type = "todoist_task_"
            if debug:
                # output unminified json in separate files
                json_object = json.dumps(s_json, indent=4)
                name = resp_type + "response" + str(self.resp_counter) + ".json"
                fullpath = os.path.join(TestHelpers.get_cassette_dir(), name)
                with open(fullpath, "w") as outfile:
                    outfile.write(json_object)
                self.resp_counter += 1

            body = json.dumps(s_json)
            response['body']['string'] = body.encode()
            return response
        return before_record_response


@pytest.fixture()
def auth_cfg(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config2")
    cfg_test = os.path.join(tmp, "auth.cfg")
    src_path = os.path.join(TestHelpers.get_root(), "source/auth.cfg")
    if os.path.exists(src_path):
        shutil.copy(src_path, cfg_test)
        os.chdir(tmp)


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
    def test(self,
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
