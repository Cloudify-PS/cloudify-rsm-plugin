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

import resource_management_sdk.profile as profile
import resource_management_sdk.data as data


class TestProfile(unittest.TestCase):

    def test_ProfileValidationError(self):
        error = profile.ProfileValidationError("a", "b", "c")

        self.assertEqual(error.message,
                         'Unknown profile validation error')
        self.assertEqual(error.resource_key, "a")
        self.assertEqual(error.requirement, "b")
        self.assertEqual(error.availability, "c")

    def test_NoAvailableResourcesError(self):
        mock = Mock()
        mock.system_name = "a"
        mock.resource_name = "b"
        mock.project_id = "c"
        error = profile.NoAvailableResourcesError(mock, "d", "e")
        self.assertEqual(error.message,
                         'Profile requirement not met for resource: a/b '
                         'in project: c. Requirement is b=d, but only e '
                         'is available')

    def test_CannotDetermineAvailabilityError(self):
        mock = Mock()
        mock.system_name = "a"
        mock.resource_name = "b"
        mock.project_id = "c"
        error = profile.CannotDetermineAvailabilityError(mock, "d", "e")
        self.assertEqual(error.message,
                         'Cannot validate profile requirement (b=d) for '
                         'resource: a/b in project: c. Availability for '
                         'this resource is not calculated.')

    def test_get_profile_from_dict_not_dict(self):
        with self.assertRaises(RuntimeError):
            profile.ResourcesProfile.get_profile_from_dict(Mock(), "check")

    def test_get_profile_from_dict_unknow_scope(self):
        profile.ResourcesProfile.get_profile_from_dict(Mock(), {
            "unknow": {
                "system": {
                    "resource": "1"
                }
            }
        })

    def test_get_profile_from_dict_global_scope(self):
        res = profile.ResourcesProfile.get_profile_from_dict(Mock(), {
            "global": {
                "system": {
                    "resource": "1"
                }
            }
        })
        self.assertEqual(res.requirements, {
            data.ResourceKey("global", "system", "resource"): 1.0})

    def test_get_profile_from_dict_wrong_value_type(self):
        res = profile.ResourcesProfile.get_profile_from_dict(Mock(), {
            "global": {
                "system": {
                    "resource": "a"
                }
            }
        })
        self.assertEqual(res.requirements, {})

    def test_get_profile_from_string(self):
        res = profile.ResourcesProfile.get_profile_from_string(
            Mock(),
            '{"global": {"system": {"resource": 5.0}}}')
        self.assertEqual(
            repr(res),
            '* [<global>, system, resource]: 5.0\n')
        self.assertEqual(res.requirements, {
            data.ResourceKey("global", "system", "resource"): 5.0})

    def test_get_profile_from_dict_wrong_project_type(self):
        with self.assertRaises(RuntimeError):
            profile.ResourcesProfile.get_profile_from_dict(Mock(), {
                "global": {
                    1: {
                        "resource": "a"
                    }
                }
            })

    def test_validate(self):
        res_prof = profile.ResourcesProfile.get_profile_from_dict(Mock(), {
            data.SCOPE_PROJECT: {
                "system": {
                    "resource": "100"
                }
            }
        })

        _ava = Mock()
        _ava.availability = 10.1
        _ctx = Mock()
        _ctx.collected_data = {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): _ava}

        # no such stats
        errors = res_prof.validate(_ctx, data.SCOPE_GLOBAL)
        self.assertEqual(len(errors), 1)
        self.assertTrue(
            isinstance(errors[0], profile.CannotDetermineAvailabilityError))

        # overcommit
        errors = res_prof.validate(_ctx, "a")
        self.assertEqual(len(errors), 1)
        self.assertTrue(
            isinstance(errors[0], profile.NoAvailableResourcesError))

        # enough resources
        _ava = Mock()
        _ava.availability = 1000
        _ctx = Mock()
        _ctx.collected_data = {data.ResourceKey(
            data.SCOPE_PROJECT, "system", "resource", "a"
        ): _ava}

        errors = res_prof.validate(_ctx, "a")
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
