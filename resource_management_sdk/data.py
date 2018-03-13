from. constants import (
    SCOPE_GLOBAL,
    SCOPE_PROJECT
)


class ResourceAvailability(object):

    def _set_values(self, quota=None, usage=None):
        if quota is not None:
            self.quota = float(quota)

        if usage is not None:
            if isinstance(usage, list):
                self.usage = float(len(usage))
            else:
                self.usage = float(usage)

        self.calculate_availability()

    def __init__(self, quota=None, usage=None):
        self.usage = None
        self.quota = None
        self.availability = None

        self._set_values(quota=quota, usage=usage)

    def update(self, quota=None, usage=None):
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

    def __repr__(self):
        return '(Q: {0}, U: {1}, A: {2})'.format(
            self.quota,
            self.usage,
            self.availability
        )


class ResourceKey(object):

    def __init__(self, scope, system_name, resource_name, project_id=None):
        self._scope = SCOPE_GLOBAL if scope == SCOPE_GLOBAL else SCOPE_PROJECT
        self._system_name = system_name
        self._resource_name = resource_name
        self._project_id = project_id

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return self.as_tuple().__hash__()

    @property
    def project_id(self):
        return self._project_id

    @property
    def resource_name(self):
        return self._resource_name

    @property
    def scope(self):
        return self._scope

    @property
    def system_name(self):
        return self._system_name

    def as_tuple(self):
        return self._project_id, self._system_name, self._resource_name

    def get_project_resource_key(self, project_id):
            return ResourceKey(
                self._scope,
                self._system_name,
                self._resource_name,
                project_id if self._scope == SCOPE_PROJECT else SCOPE_GLOBAL
            )

    def __repr__(self):
        template = '[{0}, {1}, {2}]'\
            if self._project_id \
            else '[<{0}>, {1}, {2}]'

        return template.format(
            self._project_id if self._project_id else self._scope,
            self._system_name,
            self._resource_name
        )
