from .constants import (
    NODE_TYPE_ROOT,
    PROPERTY_DEPLOYMENT_ID,
    PROPERTY_PROJECT_NAME,
    PROPERTY_RESOURCE_NAME,
    PROPERTY_RUNTIME_PROPERTY_NAME,
    PROPERTY_SCOPE,
    PROPERTY_SYSTEM_NAME,
    SCOPE_PROJECT,
    SCOPE_GLOBAL
)
from .data import (
    ResourceAvailability,
    ResourceKey
)


class Instance(object):

    @classmethod
    def _get_type(cls, type_hierarchy):
        if NODE_TYPE_ROOT in type_hierarchy:
            type_hierarchy.remove(NODE_TYPE_ROOT)

        if len(type_hierarchy) > 0:
            return type_hierarchy[0]

    def __init__(self, id, type_hierarchy, properties, runtime_properties):
        self._id = id
        self._type = self._get_type(type_hierarchy)
        self._system_name = properties.get(PROPERTY_SYSTEM_NAME)
        self._resource_name = properties.get(PROPERTY_RESOURCE_NAME, None)
        self._scope = properties.get(PROPERTY_SCOPE, SCOPE_PROJECT)
        self._runtime_property_name = properties.get(
            PROPERTY_RUNTIME_PROPERTY_NAME,
            None
        )
        self._properties = dict(properties)
        self._runtime_properties = dict(runtime_properties)

    @property
    def id(self):
        return self._id

    @property
    def properties(self):
        return self._properties

    @property
    def resource_name(self):
        return self._resource_name

    @property
    def runtime_properties(self):
        return self._runtime_properties

    @property
    def runtime_property_name(self):
        return self._runtime_property_name

    @property
    def runtime_property_value(self):
        return self._runtime_properties.get(
            self._runtime_property_name,
            None
        )

    @property
    def scope(self):
        return self._scope

    @property
    def system_name(self):
        return self._system_name

    @property
    def type(self):
        return self._type


class WorkflowCtxInstanceAdapter(Instance):

    @classmethod
    def get_instances(cls, ctx):
        return [cls(instance_ctx) for instance_ctx in ctx.node_instances]

    def __init__(self, instance_ctx):
        super(WorkflowCtxInstanceAdapter, self).__init__(
            instance_ctx.id,
            instance_ctx.node.type_hierarchy,
            instance_ctx.node.properties,
            instance_ctx._node_instance.runtime_properties
            # TODO Replace above with proper method of getting runtime_properties
            # from WorkflowNodeInstance !!!
        )


class RestClientInstanceAdapter(Instance):

    @classmethod
    def get_instances(cls, rest_client, deployment_id):
        result = []

        list_instances_response = rest_client.node_instances.list(
            deployment_id=deployment_id
        )

        for instance_response in list_instances_response:
            node_response = rest_client.nodes.get(
                deployment_id=deployment_id,
                node_id=instance_response.node_id
            )

            result.append(cls(instance_response, node_response))

        return result

    def __init__(self, instance_response, node_response):
        super(RestClientInstanceAdapter, self).__init__(
            instance_response.id,
            node_response.type_hierarchy,
            node_response.properties,
            instance_response.runtime_properties,
        )


class ResourceManagementContext(object):

    PROJECT_GLOBAL = SCOPE_GLOBAL

    def __init__(self, ctx, rest_client):
        self.logger = ctx.logger
        self.rest_client = rest_client

        self._collected_data = {}
        self._errors = {}

        self._instances = {
            self.PROJECT_GLOBAL: WorkflowCtxInstanceAdapter.get_instances(ctx)
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

    def _next_instance(self):
        project_instances = self._instances.get(self._current_project)

        if len(project_instances) > 0:
            self._current_instance = project_instances.pop()
            self._instances[self._current_project] = project_instances

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
    def collected_data(self):
        return self._collected_data

    @property
    def errors(self):
        return self._errors

    @property
    def instance(self):
        return self._current_instance

    @property
    def project(self):
        return self._current_project

    def get_resource_key(self, resource_name=None):
        return ResourceKey(
            self._current_project,
            self._current_instance.system_name,
            resource_name or self._current_instance.resource_name,
            self._current_project,
        )

    def log(self, level, message, *args):
        method = getattr(self.logger, level, None)

        if method:
            message = str(message).format(*args)
            method('[{0}] {1}'.format(self.instance.id, message))

    def log_state(self):
        self.logger.info(
            '\n=====\nCurrent {0} state: \ncurrent_project: {1} \n'
            'instances: {2} \ninstance: {3}\n====='
            .format(
                self.__class__.__name__,
                self._current_project,
                self._format_instances(),
                self._current_instance.id
            )
        )

    def next_instance(self):
        return self._next_instance()

    def resolve_project(self):
        properties = self._current_instance.properties
        deployment_id = properties.get(PROPERTY_DEPLOYMENT_ID, None)
        project_name = properties.get(PROPERTY_PROJECT_NAME, None)

        if not deployment_id:
            self.logger.warn(
                'Cannot get project instances - '
                'property {0} is not defined for node_instance {1}'
                .format(PROPERTY_DEPLOYMENT_ID, self._current_instance.id)
            )

            return False

        if not project_name:
            self.logger.warn(
                'Cannot process project instances - '
                'property {0} is not defined for node_instance {1}'
                .format(PROPERTY_PROJECT_NAME, self._current_instance.id)
            )

            return False

        instances = RestClientInstanceAdapter.get_instances(
            self.rest_client,
            deployment_id
        )

        self._instances[project_name] = instances
        self.logger.info(
            'Project {0} (deployment_id={1}) defined by node_instance {2} '
            'in parent deployment resolved successfully '
            '(got {3} node_instances from child deployment)'
            .format(
                project_name,
                deployment_id,
                self._current_instance.id,
                len(instances)
            )
        )

        return True

    def set_value(self, quota=None, usage=None, resource_name=None):
        resource_key = self.get_resource_key(resource_name)

        if resource_key in self._collected_data:
            self._collected_data[resource_key].update(
                quota=quota,
                usage=usage
            )
        else:
            self._collected_data[resource_key] = ResourceAvailability(
                quota=quota,
                usage=usage
            )
