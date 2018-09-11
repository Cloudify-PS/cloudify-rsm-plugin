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

import resource_management_sdk.data as data


class TestData(unittest.TestCase):

    def test_resource_availability_wrong(self):
        with self.assertRaises(RuntimeError):
            data.ResourceAvailability(1, 6)

    def test_resource_availability_repr(self):
        self.assertEqual(
            repr(data.ResourceAvailability(10, 5)),
            '(Q: 10.0, U: 5.0, A: 5.0)'
        )

    def test_resource_availability_dict(self):
        self.assertEqual(
            data.ResourceAvailability(10, 5).as_dict(),
            {'quota': 10.0, 'availability': 5.0, 'usage': 5.0}
        )

    def test_resource_availability_init_list(self):
        self.assertEqual(
            data.ResourceAvailability(10, [5, 1]).as_dict(),
            {'quota': 10.0, 'availability': 8.0, 'usage': 2.0}
        )

    def test_resource_availability_update(self):
        res_avaible = data.ResourceAvailability(10, [5, 1])
        res_avaible.update(usage=3)
        self.assertEqual(
            res_avaible.as_dict(),
            {'quota': 10.0, 'availability': 7.0, 'usage': 3.0}
        )

    def test_resource_key_repr(self):
        self.assertEqual(
            repr(data.ResourceKey('a', 'b', 'c', 'd')),
            '[d, b, c]'
        )

    def test_resource_key_dict(self):
        self.assertEqual(
            data.ResourceKey('a', 'b', 'c', 'd').as_dict('n'),
            {'d': {'b': {'c': 'n'}}}
        )

    def test_resource_key_hash(self):
        one = data.ResourceKey('a', 'b', 'c', 'd')
        second = data.ResourceKey('!', 'b', 'c', 'd')
        self.assertEqual(
            hash(one),
            hash(second),
        )

    def test_resource_key_get_project_resource_key(self):
        other = data.ResourceKey('a', 'b', 'c', 'n')
        self.assertEqual(
            data.ResourceKey('a', 'b', 'c', 'd').get_project_resource_key('n'),
            other
        )

    def test_resource_key_unpack(self):
        resource = data.ResourceKey('a', 'b', 'c', 'd')

        self.assertEqual(resource.project_id, 'd')
        self.assertEqual(resource.resource_name, 'c')
        self.assertEqual(resource.scope, 'project')
        self.assertEqual(resource.system_name, 'b')


if __name__ == '__main__':
    unittest.main()
