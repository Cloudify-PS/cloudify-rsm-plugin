# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest
from mock import Mock, patch

from cloudify_rest_client.exceptions import CloudifyClientError

import resource_management_sdk.execution as execution


class TestExecution(unittest.TestCase):

    @patch('time.sleep', Mock())
    def test_ExecutionRunner_get_runtime_properties(self):
        _client = Mock()
        exec_inst = execution.ExecutionRunner(Mock(), _client)

        # success
        _client.executions.get = Mock(return_value={'status': 'terminated'})
        self.assertTrue(exec_inst._check_execution_status('abc-bcd'))

        # failed
        _client.executions.get = Mock(return_value={'status': 'failed'})
        with self.assertRaises(RuntimeError):
            exec_inst._check_execution_status('abc-bcd')

        # unknow
        _client.executions.get = Mock(return_value={'status': 'unknow'})
        fake_time_values = [480, 240, 120, 60, 0]

        def fake_time(*_):
            return fake_time_values.pop()

        with patch('time.time', fake_time):
            self.assertFalse(exec_inst._check_execution_status('abc-bcd'))

        # no status
        _client.executions.get = Mock(return_value={'status': None})
        with self.assertRaises(RuntimeError):
            self.assertFalse(exec_inst._check_execution_status('abc-bcd'))

        # exeption in communication
        _client.executions.get = Mock(side_effect=CloudifyClientError('abc'))
        with self.assertRaises(RuntimeError):
            self.assertFalse(exec_inst._check_execution_status('abc-bcd'))

    @patch('time.sleep', Mock())
    def test_ExecutionRunner_run_and_wait_for_result(self):
        _client = Mock()
        _execution_start_mock = Mock()
        _execution_start_mock.id = "1234"
        exec_inst = execution.ExecutionRunner(Mock(), _client)

        _client.executions.get = Mock(return_value={'status': 'unknow'})
        _client.executions.start = Mock(return_value=_execution_start_mock)
        fake_time_values = [480, 240, 120, 60, 0]

        def fake_time(*_):
            return fake_time_values.pop()

        with patch('time.time', fake_time):
            self.assertEqual(
                exec_inst.run_and_wait_for_result('deployment_id',
                                                  'node_instance_id',
                                                  'operation_name',
                                                  'operation_inputs'),
                {})


if __name__ == '__main__':
    unittest.main()
