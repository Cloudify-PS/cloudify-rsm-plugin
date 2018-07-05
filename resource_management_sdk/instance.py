from collections import OrderedDict

from .constants import (
    NODE_TYPE_ROOT,
    PROPERTY_RESOURCE_NAME,
    PROPERTY_RUNTIME_PROPERTY_NAME,
    PROPERTY_SCOPE,
    PROPERTY_SYSTEM_NAME,
    SCOPE_GLOBAL,
    SCOPE_PROJECT
)


class Instance(object):

    @classmethod
    def _get_type(cls, type_hierarchy):
        if NODE_TYPE_ROOT in type_hierarchy:
            type_hierarchy.remove(NODE_TYPE_ROOT)

        if len(type_hierarchy) > 0:
            return type_hierarchy[0]

    def __init__(self,
                 id,
                 deployment_id,
                 type_hierarchy,
                 properties,
                 runtime_properties):

        self._id = id
        self._type = self._get_type(type_hierarchy)
        self._system_name = properties.get(PROPERTY_SYSTEM_NAME)
        self._resource_name = properties.get(PROPERTY_RESOURCE_NAME, None)
        self._scope = properties.get(PROPERTY_SCOPE, SCOPE_PROJECT)
        self._runtime_property_name = properties.get(
            PROPERTY_RUNTIME_PROPERTY_NAME,
            None
        )

        self._deployment_id = deployment_id
        self._properties = dict(properties)
        self._runtime_properties = dict(runtime_properties)
        self._execution_id = None

    @property
    def id(self):
        return self._id

    @property
    def deployment_id(self):
        return self._deployment_id

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

    @property
    def execution_id(self):
        return self._execution_id

    def set_execution_id(self, execution_id=None):
        self._execution_id = execution_id


class WorkflowCtxInstanceAdapter(Instance):

    @classmethod
    def get_instances(cls, ctx):
        return [cls(instance_ctx) for instance_ctx in ctx.node_instances]

    def __init__(self, instance_ctx):
        super(WorkflowCtxInstanceAdapter, self).__init__(
            instance_ctx.id,
            instance_ctx._node_instance.deployment_id,
            # TODO Replace above with proper method of getting deployment_id
            # TODO from WorkflowNodeInstance !!!
            instance_ctx.node.type_hierarchy,
            instance_ctx.node.properties,
            instance_ctx._node_instance.runtime_properties
            # TODO Replace above with proper method of getting runtime_properties
            # TODO from WorkflowNodeInstance !!!
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
            instance_response.deployment_id,
            node_response.type_hierarchy,
            node_response.properties,
            instance_response.runtime_properties,
        )


class Instances(object):

    PROJECT_GLOBAL = SCOPE_GLOBAL

    @classmethod
    def _prepare_operational_data(cls, initial_data):
        operational_data = []

        for project, instances in initial_data.iteritems():
            operational_data.extend(
                cls._prepare_operational_data_for_project(project, instances)
            )

        return operational_data

    @classmethod
    def _prepare_operational_data_for_project(cls, project, instances):
        operational_data = []

        for instance in instances:
            operational_data.append({
                'instance': instance,
                'project': project,
                'visited': False
            })

        return operational_data

    def __init__(self, logger, instances):
        self.logger = logger

        self._initial_data = OrderedDict({self.PROJECT_GLOBAL: instances})
        self._operational_data = []
        self._position = -1

        self.reset()

    @property
    def _current_instance(self):
        if self._position < len(self._operational_data):
            return self._operational_data[self._position]

        raise RuntimeError(
            'Unexpected Instances list state - '
            'there are {0} instances,'
            ' but current instance seems to be instance number {1}'
            .format(len(self._operational_data), self._position)
        )

    @property
    def current_instance(self):
        return self._current_instance['instance']

    @property
    def current_project(self):
        return self._current_instance['project']

    @property
    def left_instances(self):
        left_instances = OrderedDict(
            [(project, 0) for project in self._initial_data.keys()]
        )

        for instance in self._operational_data:
            if not instance['visited']:
                project = instance['project']
                left_instances[project] = left_instances.get(project, 0) + 1

        return left_instances

    def add_project(self, name, instances):
        self._initial_data[name] = instances
        self._operational_data.extend(
            self._prepare_operational_data_for_project(name, instances)
        )

    def next_instance(self):
        self._position += 1

        if self._position < len(self._operational_data):
            instance = self._operational_data[self._position]

            if instance['visited']:
                return self.next_instance()

            instance['visited'] = True
            return instance

        self.logger.info('No instances left to be processed')
        return None

    def reset(self):
        self._operational_data = self._prepare_operational_data(
            self._initial_data
        )
        self._position = -1

        return self.next_instance()

    def dump(self):
        return {
            'total': len(self._operational_data),
            'current': self._position + 1,
            'left': self.left_instances,
            'processed': [
                instance_info['instance'].id
                for instance_info in self._operational_data
                if instance_info['visited']
            ],
            'to_be_processed': [
                instance_info['instance'].id
                for instance_info in self._operational_data
                if not instance_info['visited']
            ]
        }

    def get_left_instances_info(self):
        projects_info = ''.join(
            [
                '{0}={1} |'.format(project, left_instances)
                for project, left_instances
                in self.left_instances.iteritems()
            ]
        )

        return '\n-- TOTAL: {0} \n-- CURRENT: {1} \n-- LEFT: {2} '.format(
            len(self._operational_data),
            self._position + 1,
            projects_info
        )
