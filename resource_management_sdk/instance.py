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
    """Proxy for cloudify instance class

    Attributes:
        _id: instance id
        _type: instance type
        _system_name: system name
        _resource_name: resource name
        _scope: scope name
        _runtime_property_name: runtime property name
        _deployment_id: deployment id
        _properties: instance properties
        _runtime_properties: instance runtime properties
        _execution_id: execution id"""

    @classmethod
    def _get_type(cls, type_hierarchy):
        """Get first type from type hierarchy

        Args:
            type_hierarchy: types list

        Returns:
            first non cloudify.nodes.Root type"""
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
        """Class constructor.

        Args:
            id: instance id
            deployment_id: deployment id
            type_hierarchy: string list with instance types hierarchy
            properties: instance properties
            runtime_properties: instance runtime properties"""
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
        """Instance id"""
        return self._id

    @property
    def deployment_id(self):
        """Deployment id"""
        return self._deployment_id

    @property
    def properties(self):
        """Instance properties"""
        return self._properties

    @property
    def resource_name(self):
        """Resource name"""
        return self._resource_name

    @property
    def runtime_properties(self):
        """Instance runtime properties"""
        return self._runtime_properties

    @property
    def runtime_property_name(self):
        """Instance runtime property with statatistics"""
        return self._runtime_property_name

    @property
    def runtime_property_value(self):
        """Statistics value for current instance"""
        return self._runtime_properties.get(
            self._runtime_property_name,
            None
        )

    @property
    def scope(self):
        """Instance scope"""
        return self._scope

    @property
    def system_name(self):
        """Instance system name"""
        return self._system_name

    @property
    def type(self):
        """Instance type"""
        return self._type

    @property
    def execution_id(self):
        """Execution id for last operation"""
        return self._execution_id

    def set_execution_id(self, execution_id=None):
        """Set execution id for last operation

        Args:
            execution_id: execution id for save"""
        self._execution_id = execution_id


class WorkflowCtxInstanceAdapter(Instance):
    """Proxy for cloudify workflow context class

    Attributes:
        _id: instance id
        _type: instance type
        _system_name: system name
        _resource_name: resource name
        _scope: scope name
        _runtime_property_name: runtime property name
        _deployment_id: deployment id
        _properties: instance properties
        _runtime_properties: instance runtime properties
        _execution_id: execution id"""

    @classmethod
    def get_instances(cls, ctx):
        """Get instances from context.

        Args:
            ctx: cloudify context

        Returns:
            list instances converted to current class"""
        return [cls(instance_ctx) for instance_ctx in ctx.node_instances]

    def __init__(self, instance_ctx):
        """Class constructor.

        Args:
            instance_ctx: cloudify instance context"""
        super(WorkflowCtxInstanceAdapter, self).__init__(
            instance_ctx.id,
            instance_ctx._node_instance.deployment_id,
            # TODO Replace above with proper method of getting deployment_id
            # TODO from WorkflowNodeInstance !!!
            instance_ctx.node.type_hierarchy,
            instance_ctx.node.properties,
            instance_ctx._node_instance.runtime_properties
            # TODO Replace above with proper method of getting runtime
            # TODO properties from WorkflowNodeInstance !!!
        )


class RestClientInstanceAdapter(Instance):
    """Proxy for cloudify rest client class

    Attributes:
        _id: instance id
        _type: instance type
        _system_name: system name
        _resource_name: resource name
        _scope: scope name
        _runtime_property_name: runtime property name
        _deployment_id: deployment id
        _properties: instance properties
        _runtime_properties: instance runtime properties
        _execution_id: execution id"""

    @classmethod
    def get_instances(cls, rest_client, deployment_id):
        """Get instances from context.

        Args:
            rest_client: rest client instance
            deployment_id: cloudify deployment id

        Returns:
            list instances converted to current class"""
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
        """Class constructor.

        Args:
            instance_response: cloudify instance
            node_response: cloudify instance node"""
        super(RestClientInstanceAdapter, self).__init__(
            instance_response.id,
            instance_response.deployment_id,
            node_response.type_hierarchy,
            node_response.properties,
            instance_response.runtime_properties,
        )


class Instances(object):
    """Proxy for list instances grouped by scope

    Attributes:
        logger: logger instance
        _initial_data: list of initial instances
        _operational_data: list instances for process
        _position: current position in operational_data"""

    PROJECT_GLOBAL = SCOPE_GLOBAL

    @classmethod
    def _prepare_operational_data(cls, initial_data):
        """Prepare_operational_data

        Args:
            initial_data: initial data

        Returns:
            list of prepered instances for process"""
        operational_data = []

        for project, instances in initial_data.iteritems():
            operational_data.extend(
                cls._prepare_operational_data_for_project(project, instances)
            )

        return operational_data

    @classmethod
    def _prepare_operational_data_for_project(cls, project, instances):
        """Prepare operation data for project

        Args:
            project: project name
            instances: instance list

        Returns:
            list of prepered instances for process"""
        operational_data = []

        for instance in instances:
            operational_data.append({
                'instance': instance,
                'project': project,
                'visited': False
            })

        return operational_data

    def __init__(self, logger, instances):
        """Class constructor.

        Args:
            logger: logger instance for logging
            instances: list instances"""
        self.logger = logger

        self._initial_data = OrderedDict({self.PROJECT_GLOBAL: instances})
        self._operational_data = []
        self._position = -1

        self.reset()

    @property
    def _current_instance(self):
        """Current instance for process"""
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
        """Current instance"""
        return self._current_instance['instance']

    @property
    def current_project(self):
        """Current project"""
        return self._current_instance['project']

    @property
    def left_instances(self):
        """List of unprocessed instances"""
        left_instances = OrderedDict(
            [(project, 0) for project in self._initial_data.keys()]
        )

        for instance in self._operational_data:
            if not instance['visited']:
                project = instance['project']
                left_instances[project] = left_instances.get(project, 0) + 1

        return left_instances

    def add_project(self, name, instances):
        """Add instances to processed list.

        Args:
            name: key name for instances
            instances: instances to add"""
        self._initial_data[name] = instances
        self._operational_data.extend(
            self._prepare_operational_data_for_project(name, instances)
        )

    def next_instance(self):
        """Go to next instance

        Returns:
            next instance for process"""
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
        """Reset position in process list

        Returns:
            first instance for process"""
        self._operational_data = self._prepare_operational_data(
            self._initial_data
        )
        self._position = -1

        return self.next_instance()

    def dump(self):
        """Dump current state

        Returns:
            dictionary with current interanl state"""
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
        """Dump left instances information

        Returns:
            string with list of left instances"""
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
