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

from cloudify.exceptions import NonRecoverableError
from cloudify_rest_client.exceptions import CloudifyClientError

import resource_management_plugin


class TestInit(unittest.TestCase):

    def test_get_profile_from_secret_store(self):
        rest_client = Mock()
        rest_client.secrets.get = Mock(return_value={'value': 'some_result'})

        # we have such secret
        self.assertEqual(
            resource_management_plugin._get_profile_from_secret_store(
                rest_client, 'a'),
            'some_result'
        )
        rest_client.secrets.get.assert_called_with(key='a')

        # no sudh secret
        rest_client.secrets.get = Mock(side_effect=CloudifyClientError(''))
        with self.assertRaises(NonRecoverableError):
            resource_management_plugin._get_profile_from_secret_store(
                rest_client, 'b')

    def test_get_profile(self):
        rest_client = Mock()
        rest_client.secrets.get = Mock(return_value={'value': 'some_result'})

        # profile name is not defined
        self.assertEqual(
            resource_management_plugin.get_profile(rest_client, '', 'b'),
            'b'
        )

        # use both params
        self.assertEqual(
            resource_management_plugin.get_profile(rest_client, 'a', 'b'),
            'some_result'
        )

        # empty both params
        with self.assertRaises(NonRecoverableError):
            resource_management_plugin.get_profile(rest_client, '', '')


if __name__ == '__main__':
    unittest.main()
