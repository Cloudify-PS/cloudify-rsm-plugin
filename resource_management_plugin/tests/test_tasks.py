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

from cloudify.state import current_ctx

import resource_management_plugin.tasks as tasks


class TestTasks(unittest.TestCase):

    def tearDown(self):
        current_ctx.clear()
        super(TestTasks, self).tearDown()

    def _gen_ctx(self):
        _ctx = Mock()
        current_ctx.set(_ctx)
        return _ctx

    def test_calculate_resources_availability(self):
        _ctx = self._gen_ctx()
        _ctx.node_instances = []

        rest_client = Mock()
        manager_mock = Mock()
        manager_mock.get_rest_client = Mock(return_value=rest_client)
        engine = Mock()
        engine_gen = Mock(return_value=engine)
        with patch("resource_management_plugin.tasks.manager",
                   manager_mock):
            with patch("resource_management_plugin.tasks.Engine",
                       engine_gen):
                tasks.calculate_resources_availability(ctx=_ctx)
        engine_gen.assert_called_with(_ctx, rest_client)

    def test_check_resources_availability(self):
        _ctx = self._gen_ctx()
        _ctx.node_instances = []

        rest_client = Mock()
        manager_mock = Mock()
        manager_mock.get_rest_client = Mock(return_value=rest_client)
        engine = Mock()
        engine_gen = Mock(return_value=engine)
        with patch("resource_management_plugin.tasks.manager",
                   manager_mock):
            with patch("resource_management_plugin.tasks.Engine",
                       engine_gen):
                tasks.check_resources_availability(ctx=_ctx,
                                                   project_id='project_id',
                                                   profile_str='abc')
        engine_gen.assert_called_with(_ctx, rest_client)
        engine.validate_profile.assert_called_with('project_id', 'abc')

    def test_execute_conditionally(self):
        _ctx = self._gen_ctx()
        _ctx.node_instances = []

        rest_client = Mock()
        manager_mock = Mock()
        manager_mock.get_rest_client = Mock(return_value=rest_client)
        engine = Mock()
        engine_gen = Mock(return_value=engine)
        with patch("resource_management_plugin.tasks.manager",
                   manager_mock):
            with patch("resource_management_plugin.tasks.Engine",
                       engine_gen):
                tasks.execute_conditionally(ctx=_ctx,
                                            execution_dict={'a': 'b'},
                                            project_id='project_id',
                                            profile_str='abc')
        engine_gen.assert_called_with(_ctx, rest_client)
        engine.validate_profile.assert_called_with('project_id', 'abc')
        rest_client.executions.start.assert_called_with(a='b')


if __name__ == '__main__':
    unittest.main()
