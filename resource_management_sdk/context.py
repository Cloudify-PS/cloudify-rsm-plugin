from .constants import (
    NODE_TYPE_ROOT,
    PROPERTY_SYSTEM_NAME,
    PROPERTY_RESOURCE_NAME,
    PROPERTY_SCOPE,
    SCOPE_PROJECT
)


class ResourceTypeInfo(object):

    def _set_values(self, quota=None, usage=None):
        self.quota = float(quota) if quota else None
        self.usage = None

        if usage:
            if isinstance(usage, list):
                self.usage = len(usage)
            else:
                self.usage = float(usage)

    def __init__(self, quota=None, usage=None):
        self._set_values(quota=quota, usage=usage)
        self.available = None

    def update(self, quota=None, usage=None):
        self._set_values(quota=quota, usage=usage)

    def calculate_availability(self):
        if self.quota and self.usage:
            self.available = self.quota - self.usage

    def __repr__(self):
        return '(Q: {0}, U: {1}, A: {2})'.format(
            self.quota,
            self.usage,
            self.available
        )


class ResourceManagementContext(object):

    @classmethod
    def _get_instances(cls, ctx):
        return []

    @classmethod
    def _get_resource_management_type(cls, instance):
        return None

    def __init__(self, ctx):
        self.logger = ctx.logger

        self._instances = iter(self._get_instances(ctx))
        self._projects = [] # TODO list of ProxyResourceManagementContext ??
        self._values = {}

        self._next()

    def _log_state(self):
        self.logger.info(
            'Current {0} state: \ninstance: {1} \nsystem_name: {2} \n'
            'resource_name: {3} \nscope: {4} \ntype: {5}'
            .format(
                self.__class__.__name__,
                self._instance.id,
                self._system_name,
                self._resource_name,
                self._scope,
                self._type
            )
        )

    # TODO adjust to instances got both from context and rest_client
    def _next(self):
        try:
            instance = next(self._instances)
        except StopIteration:
            # TODO: check if in self._projects are some project-context and return its instances ?
            return False

        self._instance = instance
        self._node = instance.node

        self._system_name = self._node.properties.get(
            PROPERTY_SYSTEM_NAME
        )
        self._resource_name = self._node.properties.get(
            PROPERTY_RESOURCE_NAME,
            None
        )
        self._scope = self._node.properties.get(
            PROPERTY_SCOPE,
            SCOPE_PROJECT
        )

        self._type = self._get_resource_management_type(instance)

        self._log_state()
        return True

    @property
    def system_name(self):
        return self._system_name

    @property
    def resource_name(self):
        return self._resource_name

    @property
    def scope(self):
        return self._scope

    @property
    def type(self):
        return self._type

    @property
    def projects(self):
        return self._projects

    @property
    def values(self):
        return self._values

    def mark_as_project(self):
        self._projects.append(self._instance)

    def next_instance(self):
        return self._next()

    def set_result(self, quota=None, usage=None):
        key = ('global', self._system_name, self._resource_name) # TODO project recognition

        if key in self._values:
            self._values[key].update(quota=quota, usage=usage)
        else:
            self._values[key] = ResourceTypeInfo(quota=quota, usage=usage)


class DeploymentResourceManagementContext(ResourceManagementContext):

    @classmethod
    def _get_instances(cls, ctx):
        return list(ctx.node_instances)

    @classmethod
    def _get_resource_management_type(cls, instance):
        type_hierarchy = instance.node.type_hierarchy

        if NODE_TYPE_ROOT in type_hierarchy:
            type_hierarchy.remove(NODE_TYPE_ROOT)

        if len(type_hierarchy) > 0:
            return type_hierarchy[0]


class ProxyResourceManagementContext(ResourceManagementContext):
    pass
