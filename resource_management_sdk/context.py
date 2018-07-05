import collections

from .constants import (
    DEFAULT_OPERATION_NAME,
    PROPERTY_DEPLOYMENT_ID,
    PROPERTY_OPERATION_INPUTS,
    PROPERTY_PROJECT_NAME
)
from .data import (
    ResourceAvailability,
    ResourceKey
)
from .execution import ExecutionRunner
from .instance import (
    Instances,
    RestClientInstanceAdapter,
    WorkflowCtxInstanceAdapter
)


class ResourceManagementContext(object):

    def __init__(self, ctx, rest_client):
        self.logger = ctx.logger
        self.rest_client = rest_client
        self.execution_runner = ExecutionRunner(self.log, rest_client)

        self._collected_data = {}
        self._instances = Instances(
            ctx.logger,
            WorkflowCtxInstanceAdapter.get_instances(ctx)
        )
        self._result_instance_ids = []

    @property
    def collected_data(self):
        result = {}

        for resource_key, resource_data in self._collected_data.iteritems():
            if resource_data.availability:
                result[resource_key] = resource_data

        return result

    @property
    def collected_data_dict(self):
        def merge(dst, src):
            for k, v in src.iteritems():
                if k in dst and \
                        isinstance(dst[k], dict) and \
                        isinstance(src[k], collections.Mapping):
                    merge(dst[k], src[k])
                else:
                    dst[k] = src[k]

        result = {}

        for resource_key, resource_data in self.collected_data.iteritems():
            merge(result, resource_key.as_dict(resource_data.as_dict()))

        return result

    @property
    def collected_data_raw(self):
        return self._collected_data

    @property
    def instance(self):
        return self._instances.current_instance

    @property
    def project(self):
        return self._instances.current_project

    @property
    def result_instances(self):
        return self._result_instance_ids

    def get_resource_key(self, resource_name=None):
        return ResourceKey(
            self.project,
            self.instance.system_name,
            resource_name or self.instance.resource_name,
            self.project,
        )

    def log(self, level, message, *args):
        method = getattr(self.logger, level, None)

        if method:
            message = str(message).format(*args)
            method('[{0}] {1}'.format(self.instance.id, message))

    def log_state(self):
        self.logger.info(
            '\n\nCurrent {0} state: \ncurrent_project: {1} \n'
            'instances: {2} \ninstance: {3}\n'
            .format(
                self.__class__.__name__,
                self.project,
                self._instances.get_left_instances_info(),
                self.instance.id
            )
        )

    def next_instance(self):
        instance = self._instances.next_instance()
        if instance:
            self.log_state()

        return instance

    def reset(self):
        instance = self._instances.reset()
        if instance:
            self.log_state()

        return instance

    def resolve_project(self):
        properties = self.instance.properties
        deployment_id = properties.get(PROPERTY_DEPLOYMENT_ID, None)
        project_name = properties.get(PROPERTY_PROJECT_NAME, None)

        if not deployment_id:
            self.logger.warn(
                'Cannot get project instances - '
                'property {0} is not defined for node_instance {1}'
                .format(PROPERTY_DEPLOYMENT_ID, self.instance.id)
            )

            return False

        if not project_name:
            self.logger.warn(
                'Cannot process project instances - '
                'property {0} is not defined for node_instance {1}'
                .format(PROPERTY_PROJECT_NAME, self.instance.id)
            )

            return False

        instances = RestClientInstanceAdapter.get_instances(
            self.rest_client,
            deployment_id
        )

        self._instances.add_project(project_name, instances)
        self.logger.info(
            'Project {0} (deployment_id={1}) defined by node_instance {2} '
            'in parent deployment resolved successfully '
            '(got {3} node_instances from child deployment)'
            .format(
                project_name,
                deployment_id,
                self.instance.id,
                len(instances)
            )
        )

        return True

    def run_execution(self, operation_name=DEFAULT_OPERATION_NAME, wait=True):
        execution_id = self.execution_runner.run(
            self.instance.deployment_id,
            self.instance.id,
            operation_name,
            self.instance.properties.get(
                PROPERTY_OPERATION_INPUTS,
                {}
            )
        )

        self.instance.set_execution_id(execution_id)

        if wait:
            result = self.execution_runner.wait_for_result(
                execution_id,
                self.instance.id
            )

            self.instance.set_execution_id()
            return result

        return execution_id

    def get_execution_result(self):
        return self.execution_runner.wait_for_result(
            self.instance.execution_id,
            self.instance.id
        )

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

    def set_runtime_properties(self,
                               runtime_properties,
                               instance_id=None,
                               update=False):

        if not instance_id:
            instance_id = self.instance.id

        instance_data = self.rest_client.node_instances.get(instance_id)
        version = instance_data['version']

        if update:
            runtime_properties.update(
                instance_data['runtime_properties']
            )

        self.logger.debug(
            'Setting {0} runtime_properties for '
            'node_instance: {1} with version: {2}'
            .format(runtime_properties, instance_id, version)
        )

        self.rest_client.node_instances.update(
            instance_id or self.instance.id,
            runtime_properties=runtime_properties,
            version=version
        )

    def add_result_instance_id(self, instance_id=None):
        if not instance_id:
            instance_id = self.instance.id

        if instance_id not in self._result_instance_ids:
            self._result_instance_ids.append(instance_id)

    def dump(self):
        return {
            'instances': self._instances.dump(),
            'availability': self.collected_data_dict
        }
