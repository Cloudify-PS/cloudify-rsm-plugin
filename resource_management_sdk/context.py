from .constants import (
    NODE_TYPE_ROOT,
    PROPERTY_SYSTEM_NAME,
    PROPERTY_RESOURCE_NAME,
    PROPERTY_SCOPE,
    SCOPE_PROJECT,
    SCOPE_GLOBAL
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

        self.calculate_availability()

    def __init__(self, quota=None, usage=None):
        self._set_values(quota=quota, usage=usage)
        self.available = None

    def update(self, quota=None, usage=None):
        self._set_values(quota=quota, usage=usage)
        self.calculate_availability()

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

    PROJECT_GLOBAL = SCOPE_GLOBAL

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

    def __init__(self, ctx):
        self.logger = ctx.logger

        self._collected_data = {}
        self._instances = {
            self.PROJECT_GLOBAL: self._get_instances(ctx)
        }

        self._current_project = self.PROJECT_GLOBAL
        self._next_instance()

    def _format_instances(self):
        return ''.join(
            [
                '{0}={1} |'.format(k, len(v))
                for k, v
                in self._instances.iteritems()
            ]
        )

    # TODO adjust to instances got both from context and rest_client
    def _next_instance(self):
        project_instances = self._instances.get(self._current_project)

        if len(project_instances) > 0:
            self._instance = project_instances.pop()
            self._instances[self._current_project] = project_instances

            # TODO START move to separate Instance class
            self._system_name = self._instance.node.properties.get(
                PROPERTY_SYSTEM_NAME
            )
            self._resource_name = self._instance.node.properties.get(
                PROPERTY_RESOURCE_NAME,
                None
            )
            self._scope = self._instance.node.properties.get(
                PROPERTY_SCOPE,
                SCOPE_PROJECT
            )

            self._type = self._get_resource_management_type(self._instance)
            # TODO END move to separate Instance class

            self.log_state()
            return True
        else:
            return self._next_project()

    def _next_project(self):
        self._instances.pop(self._current_project)
        projects = self._instances.keys()

        if len(projects) == 0:
            self.logger.info('No projects left to be processed')
            return False

        self._current_project = projects[0]
        return self._next_instance()

    @property
    def current_project(self):
        return self._current_project

    @property
    def collected_data(self):
        return self._collected_data

    # TODO (re)move
    @property
    def system_name(self):
        return self._system_name

    # TODO (re)move
    @property
    def resource_name(self):
        return self._resource_name

    # TODO (re)move
    @property
    def scope(self):
        return self._scope

    # TODO (re)move
    @property
    def type(self):
        return self._type

    def log_state(self):
        self.logger.info(
            'Current {0} state: \ncurrent_project: {1} \n'
            'instances: {2} \ninstance: {3}'
            .format(
                self.__class__.__name__,
                self._current_project,
                self._format_instances(),
                self._instance.id
            )
        )

    def next_instance(self):
        return self._next_instance()

    # TODO
    def resolve_project(self):
        self.logger.info(
            'TODO: Use CloudifyRestClient to get instances for deployment'
        )

    def set_result(self, quota=None, usage=None):
        key = (self._current_project, self._system_name, self._resource_name)

        if key in self._collected_data:
            self._collected_data[key].update(quota=quota, usage=usage)
        else:
            self._collected_data[key] = ResourceTypeInfo(
                quota=quota,
                usage=usage
            )
