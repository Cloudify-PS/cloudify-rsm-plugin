import json

from .constants import SCOPES
from .data import ResourceKey


class ProfileValidationError(object):
    """Profile validation error base class

    Attributes:
        resource_key: Resource key value
        requirement: Requirement value
        availability: Availability"""

    MESSAGE_TEMPLATE = 'Unknown profile validation error'

    def __init__(self,
                 resource_key,
                 requirement,
                 availability=None):
        """Class constructor.

        Args:
            resource_key: Resource key value
            requirement: Requirement value
            availability: Availability"""
        self.resource_key = resource_key
        self.requirement = requirement
        self.availability = availability

    @property
    def message(self):
        """Error as string"""
        return self.MESSAGE_TEMPLATE


class NoAvailableResourcesError(ProfileValidationError):
    """No Available Resources Error"""

    MESSAGE_TEMPLATE = 'Profile requirement not met for resource: ' \
                       '{0}/{1} in project: {2}. ' \
                       'Requirement is {1}={3}, but only {4} is available'

    @property
    def message(self):
        """Error as string"""
        return self.MESSAGE_TEMPLATE.format(
            self.resource_key.system_name,
            self.resource_key.resource_name,
            self.resource_key.project_id,
            self.requirement,
            self.availability
        )


class CannotDetermineAvailabilityError(ProfileValidationError):
    """Cannot Determine Availability Error"""

    MESSAGE_TEMPLATE = 'Cannot validate profile requirement ({0}={1}) for ' \
                       'resource: {2}/{0} in project: {3}. ' \
                       'Availability for this resource is not calculated.'

    @property
    def message(self):
        """Error as string"""
        return self.MESSAGE_TEMPLATE.format(
            self.resource_key.resource_name,
            self.requirement,
            self.resource_key.system_name,
            self.resource_key.project_id
        )


class ResourcesProfile(object):
    """Resources Profile as storage for requirement for resourses.

    Attributes:
        _logger: logger instance
        _requirements_data: requirements data dictionary"""

    @classmethod
    def get_profile_from_dict(cls, logger, profile_dict):
        """Convert requirements dictionary to profile.

        Args:
            logger: logger for internal use
            profile_dict: source for profile filling, e.g.:
                {
                    "project": {
                        "system": {
                            "resource": "1"
                        }
                    }
                }

        Returns:
            Profile instance with requirements.

        Raises:
            RuntimeError: Wrong structure of requirements dictionary."""

        def is_str(value):
            if not isinstance(value, basestring):
                raise RuntimeError(
                    'Wrong key: {} in profile definition. '
                    'Keys may be only string type.'
                    .format(value)
                )

        def is_dict(value):
            if not isinstance(value, dict):
                raise RuntimeError(
                    'Cannot process profile definition (part) '
                    'defined in unknown type: {}. '
                    'Only dict (parsed JSON) is supported.'
                    .format(type(value))
                )

        is_dict(profile_dict)
        profile = ResourcesProfile(logger)

        for scope, scope_subdict in profile_dict.iteritems():
            is_str(scope)
            is_dict(scope_subdict)

            for system_name, system_subdict in scope_subdict.iteritems():
                is_str(system_name)
                is_dict(system_subdict)

                for resource_name, requirement_value \
                        in system_subdict.iteritems():
                    is_str(resource_name)

                    profile.add_requirement(
                        scope,
                        system_name,
                        resource_name,
                        requirement_value
                    )

        return profile

    @classmethod
    def get_profile_from_string(cls, logger, profile_str):
        """Convert requirements dictionary to profile.

        Args:
            logger: logger for internal use
            profile_str: json string for profile filling, e.g.:
                '{"global": {"system": {"resource": 5.0}}}'

        Returns:
            Profile instance with requirements.

        Raises:
            RuntimeError: Wrong structure of requirements dictionary."""
        return cls.get_profile_from_dict(logger, json.loads(profile_str))

    def __init__(self, logger):
        """Class constructor.

        Args:
            logger: internal loger for use in calls."""
        self._logger = logger
        self._requirements_data = {}

    @property
    def requirements(self):
        """Current state of internal requirements dictionary.

        Returns:
            Current requirements dictionary."""
        return self._requirements_data

    def add_requirement(self, scope, system_name, resource_name, value):
        """Add requirement.

        Args:
            scope: scope name
            system_name: system name
            resource_name: resource name
            value: requirement convertable to float. Any not float converable
                ignored without exception raising.

        Returns:
            None"""
        if scope not in SCOPES:
            self._logger.warn(
                'Invalid profile requirement scope: {0} (possible values: {1})'
                .format(scope, SCOPES)
            )

            return

        resource_key = ResourceKey(scope, system_name, resource_name)

        try:
            self._requirements_data[resource_key] = float(value)
        except (TypeError, ValueError):
            self._logger.warn(
                'Invalid profile requirement value: {0}. It must be a number'
                .format(value)
            )

    def validate(self, rsm_ctx, project_id):
        """Validate current resource managment context instance by current
        profile.

        Args:
            rsm_ctx: resource managment context instance
            project_id: project name for validate

        Returns:
            List of errors, can be:
                NoAvailableResourcesError,
                CannotDetermineAvailabilityError"""
        errors = []
        self._logger.info(
            'Profile validation started for "{}" project'.format(project_id)
        )

        for resource_key, requirement_value in \
                self._requirements_data.iteritems():

            project_resource_key = resource_key.get_project_resource_key(
                project_id
            )
            availability_data = rsm_ctx.collected_data.get(
                project_resource_key,
                None
            )

            rsm_ctx.logger.debug(
                'Availability data got for {0} is: {1}'
                .format(project_resource_key, availability_data)
            )

            if not availability_data:
                errors.append(
                    CannotDetermineAvailabilityError(
                        project_resource_key,
                        requirement_value
                    )
                )

                continue

            if requirement_value > availability_data.availability:
                errors.append(
                    NoAvailableResourcesError(
                        project_resource_key,
                        requirement_value,
                        availability_data.availability
                    )
                )

        return errors

    def __repr__(self):
        """Dump current requirements in profile.

        Returns:
            String with human-readable list of requirements."""
        return ''.join(
            '* {0}: {1}\n'.format(k, v)
            for k, v
            in self._requirements_data.iteritems()
        )
