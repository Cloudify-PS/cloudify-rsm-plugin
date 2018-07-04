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
        self._errors = {}
        self._instances = Instances(
            ctx.logger,
            WorkflowCtxInstanceAdapter.get_instances(ctx)
        )

    @property
    def collected_data(self):
        return self._collected_data

    @property
    def errors(self):
        return self._errors

    @property
    def instance(self):
        return self._instances.current_instance

    @property
    def project(self):
        return self._instances.current_project

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
