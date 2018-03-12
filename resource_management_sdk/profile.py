from .constants import (
    SCOPE_GLOBAL,
    SCOPE_PROJECT,
    SCOPES
)
from .data import ResourceKey


class ProfileValidationError(object):

    MESSAGE_TEMPLATE = 'Unknown profile validation error'

    def __init__(self,
                 resource_key,
                 requirement,
                 availability=None):

        self._resource_key = resource_key
        self._requirement = requirement
        self._availability = availability

    @property
    def availability(self):
        return self._availability

    @property
    def message(self):
        return self.MESSAGE_TEMPLATE

    @property
    def resource_key(self):
        return self._resource_key

    @property
    def requirement(self):
        return self._requirement


class NoAvailableResourcesError(ProfileValidationError):

    MESSAGE_TEMPLATE = 'Profile requirement not met for resource: ' \
                       '{0}/{1} in project: {2}. ' \
                       'Requirement is {1}={3}, but only {4} is available'

    @property
    def message(self):
        return self.MESSAGE_TEMPLATE.format(
            self._resource_key.system_name,
            self._resource_key.resource_name,
            self._resource_key.project_id,
            self._requirement,
            self._availability
        )


class CannotDetermineAvailabilityError(ProfileValidationError):

    MESSAGE_TEMPLATE = 'Cannot validate profile requirement ({0}={1}) for resource: ' \
                       '{2}/{0} in project: {3}. ' \
                       'Availability for this resource is not calculated.'

    @property
    def message(self):
        return self.MESSAGE_TEMPLATE.format(
            self._resource_key.resource_name,
            self._requirement,
            self._resource_key.system_name,
            self._resource_key.project_id
        )


class ResourcesProfile(object):

    @staticmethod
    def get_profile_from_dict(logger, profile_dict):
        pass

    @staticmethod
    def get_profile_from_string(logger, profile_str):
        # TODO
        profile = ResourcesProfile(logger)
        profile.add_requirement(SCOPE_GLOBAL, 'apic', 'bd', 1.0)
        profile.add_requirement(SCOPE_GLOBAL, 'apic', 'vrf', 1.0)
        profile.add_requirement(SCOPE_PROJECT, 'apic', 'contract', 2.0)
        profile.add_requirement(SCOPE_PROJECT, 'apic', 'epg', 2.0)

        return profile

    def __init__(self, logger):
        self._logger = logger
        self._requirements_data = {}

    @property
    def requirements(self):
        return self._requirements_data

    def add_requirement(self, scope, system_name, resource_name, value):
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
        errors = []
        self._logger.info(
            'Validating profile for "{}" project'.format(project_id)
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
