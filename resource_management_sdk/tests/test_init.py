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
from mock import Mock
from collections import OrderedDict

from cloudify.exceptions import NonRecoverableError

import resource_management_sdk.data as data
import resource_management_sdk as sdk


class TestInit(unittest.TestCase):

    def _get_engine(self):
        _instances_ctx = Mock()
        _instances_ctx.id = 'id'
        _instances_ctx.logger = Mock()
        _instances_ctx._node_instance.deployment_id = 'deployment_id'
        _instances_ctx.node.type_hierarchy = ['cloudify.nodes.Root', 'a']
        _instances_ctx.node.properties = {'system_name': 'system',
                                          'resource_name': 'resource',
                                          'scope': 'scope',
                                          'runtime_property_name': "c"}
        _instances_ctx._node_instance.runtime_properties = {'resource': 'b',
                                                            'c': 'd'}
        _ctx = Mock()
        _client = Mock()
        _ctx.node_instances = [_instances_ctx]
        engine = sdk.Engine(_ctx, _client)
        return engine, _client, _ctx, _instances_ctx

    def test_Engine_init(self):
        engine, _client, _ctx, _instances_ctx = self._get_engine()
        self.assertEqual(engine.rsm_ctx.instance.id, 'id')
        self.assertEqual(engine.rsm_ctx.project, 'global')
        self.assertEqual(engine.rsm_ctx.result_instances, [])
        engine.rsm_ctx.add_result_instance_id()
        engine.rsm_ctx.add_result_instance_id('abc')
        self.assertEqual(engine.rsm_ctx.result_instances, ['id', 'abc'])
        self.assertEqual(engine.rsm_ctx.collected_data_raw, {})
        self.assertEqual(engine.rsm_ctx.dump(), {
            'availability': {},
            'instances': {
                'current': 1,
                'left': OrderedDict([('global', 0)]),
                'processed': ['id'],
                'to_be_processed': [],
                'total': 1}})

    def test_Engine_get_profile(self):
        engine, _client, _ctx, _instances_ctx = self._get_engine()
        res = engine._get_profile('{"global": {"system": {"resource": 5.0}}}')
        self.assertEqual(
            repr(res),
            '* [<global>, system, resource]: 5.0\n')

    def test_Engine_validate_profile(self):
        engine, _client, _ctx, _instances_ctx = self._get_engine()

        # over limit
        with self.assertRaises(NonRecoverableError):
            engine.validate_profile(
                "abc", '{"global": {"system": {"resource": 5.0}}}', True)

        # under limit
        engine.rsm_ctx._collected_data = {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): data.ResourceAvailability(100, 1)}
        res = engine.validate_profile(
            "abc", '{"a": {"system": {"resource": 5.0}}}', True)
        self.assertEqual(res, [])

    def test_Engine_report_data(self):
        engine, _client, _ctx, _instances_ctx = self._get_engine()
        engine._report_data()
        engine.logger.info.assert_called_with(
            '\nCalculated resources availabilities: \n')

    def test_Engine_set_result_as_runtime_properties(self):
        engine, _client, _ctx, _instances_ctx = self._get_engine()
        engine.rsm_ctx._result_instance_ids = ["first"]
        _client.node_instances.update = Mock()
        _client.node_instances.get = Mock(return_value={
            'version': 11,
            'runtime_properties': {'a': 'b'}
        })
        _error = Mock()
        _error.message = "NoNeOfSuCh"
        engine._set_result_as_runtime_properties([_error])
        _client.node_instances.get.assert_called_with('first')
        _client.node_instances.update.assert_called_with(
            'first', runtime_properties={
                'a': 'b', 'errors': ['NoNeOfSuCh']
            }, version=11)

    def test_Engine_run(self):
        engine, _client, _ctx, _instances_ctx = self._get_engine()

        # run several
        engine.run(sdk.PARALLEL_EXECUTIONS_HANDLER_CHAIN)

        # run one
        engine.run([sdk.ResultHandler])

        # use fully custom handler
        our_magic_handler = Mock()
        our_magic_handler.can_handle = Mock(return_value=True)
        our_magic_handler_type = Mock(return_value=our_magic_handler)
        engine.run([our_magic_handler_type])
        our_magic_handler_type.assert_called_with(engine.logger)
        our_magic_handler.can_handle.assert_called_with(engine.rsm_ctx)


if __name__ == '__main__':
    unittest.main()
