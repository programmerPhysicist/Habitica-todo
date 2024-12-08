# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name, import-error
# integration test for one_way_sync.py
import pickle
from datetime import datetime
from dateutil.tz import tzutc
import pytest
import vcr
import requests
from mockito import when, mock, unstub, when2, verify, captor, ANY, arg_that
from one_way_sync import sync_todoist_to_habitica
from todoist_api_python import models
from hab_task import HabTask
# from common_fixtures import empty_pickle, fake_config_file, mock_web_calls # pylint: disable=unused-import
# pylint: enable=invalid-name

'''
def get_todo_task():
    # create todoist task
    created_at = '1987-11-04T09:54:16.1134110Z'
    due_dict = {'date': '2024-12-19',
                'datetime': None,
                'is_recurring': False,
                'string': 'Dec 19',
                'timezone': None}
    duedate = models.Due.from_dict(due_dict)

    todoist_task = models.Task(None,  # assignee_id
                               None,  # assigner_id
                               0,     # comment_count
                               False, # is_completed
                               'Test task 1', # content
                               created_at,    # created_at
                               '59292300',    # creator_id
                               '',            # description
                               duedate,       # due
                               '96935939',    # id
                               [],            # labels
                               0,             # order
                               None,          # parent_id
                               1,             # priority
                               '9187482462',  # project_id
                               '19099659',    # section_id
                               None,          # url
                               ''             # duration
                               )
    return todoist_task


def get_hab_task():
    hab_task = {'text': 'Test task 1', 'priority': '1.5', 'attribute': '',
                'type': 'todo',
                '_id': 'a94e8f46-5c14-f14a-f189-e669e239730a',
                'completed': False, 'alias': '96935939',
                'date': '2024-12-19T00:00:00.000Z',
                'due': datetime(2024, 12, 19)}
    return hab_task


def case1():
    empty_val = {"data": []}

    hab_task = get_hab_task()
    hab_task['due'] = datetime(2024, 12, 20, tzinfo=tzutc())
    hab_dict = {"data": [hab_task]}

    todo_tasks = [get_todo_task()]
    completed_todos = []

    inputs = {'hab_task': hab_dict,
              'completed_habs': empty_val,
              'todo_tasks': todo_tasks,
              'done_tasks': completed_todos}

    return inputs


def simple_pickle():
    hab = HabTask(get_hab_task())
    match_dict = {'96935939': {'todo': get_todo_task(),
                               'hab': hab,
                               'recurs': 'No'
                               }
                  }
    inputs = {'pickle_tasks': match_dict}
    return inputs


# pylint: disable=missing-class-docstring

class TestSyncDate:
    block_vcr = vcr.VCR(
        serializer='json',
        cassette_library_dir='/tmp',
        record_mode='none'
    )

    # pylint: disable=redefined-outer-name, unused-argument, too-many-locals, too-few-public-methods
    @pytest.mark.parametrize("mock_web_calls", [case1()], indirect=True)
    @pytest.mark.parametrize("pickle_in", [simple_pickle()], indirect=True)
    def test(self,
             fake_config_file,
             mock_web_calls,
             pickle_in):
        # pylint: enable=redefined-outer-name, unused-argument

        # set default response
        response = mock({'status': 200, 'ok': True}, spec=requests.Response)

        # mock out post to Habitica
        # when(requests).post(...).thenReturn(response)

        # mock out put to Habitica
        when(requests).put(...).thenReturn(response)

        # mock out web call to get id
        hab_task = {'text': 'Some test task', 'priority': '', 'attribute': '',
                    'type': 'todo', '_id': 'a94e8f46-5c14-f14a-f189-e669e239730a',
                    'completed': False, 'alias': '96935939'}
        hab_val2 = {"data": hab_task}


        response2 = mock({'status': 200, 'ok': True}, spec=requests.Response)
        task_url = 'https://habitica.com/api/v3/tasks/8296278113'
        when(requests).get(headers={'url': 'https://habitica.com',
                                    'x-api-user': 'cd18fc9f-b649-4384-932a-f3bda6fe8102',
                                    'x-api-key': '18f22441-2c87-6d8e-fb2a-3fa670837b5a'},
                           url=task_url).thenReturn(response2)
        when(response2).json().thenReturn(hab_val2)

        # mock dump of pickle file
        pkl_out = mock()
        pkl_file = mock()
        when2(open, ...).thenCallOriginalImplementation()
        when2(open, 'oneWay_matchDict.pkl', 'wb').thenReturn(pkl_file)
        when(pickle).Pickler(...).thenReturn(pkl_out)
        when(pkl_out).dump(...)

        # using get_all_habtasks() which contains requests.get(), uses the monkeypatch
        with self.block_vcr.use_cassette('dump.json'):
            sync_todoist_to_habitica()

        # verify post request
        the_url = captor(ANY(str))
        the_data = captor(ANY(dict))
        the_headers = captor(ANY(dict))

        verify(requests, times=1).post(url='https://habitica.com/api/v3/tasks/user/',
                                       data=arg_that(verify_post_request),
                                       headers=the_headers)

        # verify put request
        the_url = captor(ANY(str))
        verify(requests, times=1).put(headers=the_headers, url=the_url, data=the_data)

        # verify pickle dump
        dump_dict = captor(ANY(dict))
        verify(pkl_out, times=1).dump(dump_dict)

        # clean-up
        unstub()'''
