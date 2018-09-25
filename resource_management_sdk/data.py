from. constants import (
    SCOPE_GLOBAL,
    SCOPE_PROJECT
)


class ResourceAvailability(object):
    """Storage for availability information

    Attributes:
        usage: usage value
        quota: quota value
        availability: availability value"""

    def _set_values(self, quota=None, usage=None):
        """Recalculate availability information.

        Args:
            quota: optional, quota for set,
            usage: optional, usage for set."""
        if quota is not None:
            self.quota = float(quota)

        if usage is not None:
            if isinstance(usage, list):
                self.usage = float(len(usage))
            else:
                self.usage = float(usage)

        self.calculate_availability()

    def __init__(self, quota=None, usage=None):
        """Class constructor.

        Args:
           quota: optional, quota value
           usage: optional, usage value"""
        self.usage = None
        self.quota = None
        self.availability = None

        self._set_values(quota=quota, usage=usage)

    def update(self, quota=None, usage=None):
        """Update availability information.

        Args:
            quota: optional, quota for set,
            usage: optional, usage for set."""
        self._set_values(quota=quota, usage=usage)
        self.calculate_availability()

    def calculate_availability(self):
        if self.quota is not None and self.usage is not None:
            if self.quota >= 0.0:
                self.availability = self.quota - self.usage

        if self.availability and self.availability < 0.0:
            raise RuntimeError(
                'Resource availability cannot be lower than 0 !! '
                '(calculated {0} for quota={1} and usage={2})'
                .format(self.availability, self.quota, self.usage)
            )

    def as_dict(self):
        """Dump current quota/usage inforamation as dictionary.

        Returns:
            dictionary as {'quota': <quota_value>,
                           'usage': <usage_value>,
                           'availability': <availability_value>}"""
        return {
            'quota': self.quota,
            'usage': self.usage,
            'availability': self.availability
        }

    def __repr__(self):
        """Dump current quota/usage inforamation as string.

        Returns:
            string like as:
                (Q: <quota>, U: <usage>, A: <availability>)"""
        return '(Q: {0}, U: {1}, A: {2})'.format(
            self.quota,
            self.usage,
            self.availability
        )


class ResourceKey(object):
    """Storage for scope/system/resource name

    Attributes:
        _scope: scope name
        _system_name: system_name
        _resource_name: resource_name
        _project_id: project id"""

    def __init__(self, scope, system_name, resource_name, project_id=None):
        """Class constructor.

        Args:
            scope: scope name
            system_name: system name
            resource_name: resource name
            project_id: optional, project id"""
        self._scope = SCOPE_GLOBAL if scope == SCOPE_GLOBAL else SCOPE_PROJECT
        self._system_name = system_name
        self._resource_name = resource_name
        self._project_id = project_id

    def __eq__(self, other):
        """Compare current resource with other instance

        Args:
            other: object for compare

        Returns:
            True, if objects are equal"""
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        """Get hash value for current object.

        Returns:
            hash value"""
        return self.as_tuple().__hash__()

    @property
    def project_id(self):
        """Returns project name."""
        return self._project_id

    @property
    def resource_name(self):
        """Returns resource name"""
        return self._resource_name

    @property
    def scope(self):
        """"Returns scope name"""
        return self._scope

    @property
    def system_name(self):
        """"Returns system name"""
        return self._system_name

    def as_dict(self, value):
        """Get resource key as dictionary

        Args:
            value: value for set

        Returns:
            dictionary like:
                {
                    <scope>: {
                        <system>: {
                            <resource>: <value>}}}"""
        return {
            self._project_id or self._scope: {
                self._system_name: {
                    self._resource_name: value
                }
            }
        }

    def as_tuple(self):
        """Get resource key as tuple

        Returns:
            tuple like: <project>, <system>, <resource>"""
        return self._project_id, self._system_name, self._resource_name

    def get_project_resource_key(self, project_id):
        """Return resource key by project.

        Args:
            project_id: project for use in resource key

        Returns:
            resource key"""
        return ResourceKey(
                self._scope,
                self._system_name,
                self._resource_name,
                project_id if self._scope == SCOPE_PROJECT else SCOPE_GLOBAL
            )

    def __repr__(self):
        """Dump resource key as string.

        Returns:
            string like as: [<scope>, <system>, <resource>]"""
        template = '[{0}, {1}, {2}]'\
            if self._project_id \
            else '[<{0}>, {1}, {2}]'

        return template.format(
            self._project_id if self._project_id else self._scope,
            self._system_name,
            self._resource_name
        )
