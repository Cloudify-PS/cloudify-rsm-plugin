import time

from cloudify_rest_client.exceptions import CloudifyClientError


class ExecutionStatusPoller(object):

    DEFAULT_SUCCESS_STATUSES = ['terminated', 'cancelled']
    DEFAULT_FAILURE_STATUSES = ['failed']
    DEFAULT_INTERVAL = 5
    DEFAULT_TIMEOUT = 180

    def __init__(self, logger_method, rest_client, **kwargs):
        self.logger_method = logger_method
        self.rest_client = rest_client

        _timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self._timeout = float('infinity') if _timeout == -1 else _timeout
        self._interval = kwargs.get('interval', self.DEFAULT_INTERVAL)

        self._success_statuses = kwargs.get(
            'success_statuses',
            self.DEFAULT_SUCCESS_STATUSES
        )

        self._failure_statuses = kwargs.get(
            'failure_statuses',
            self.DEFAULT_FAILURE_STATUSES
        )

    def _check_execution_status(self, execution_id):
        try:
            execution = self.rest_client.executions.get(
                execution_id=execution_id
            )
        except CloudifyClientError as e:
            raise RuntimeError(
                'Error during polling execution {0} state. Details: {1}.'
                .format(execution_id, str(e))
            )

        execution_status = execution.get('status', None)

        if not execution_status:
            raise RuntimeError(
                'Failed to retrieve status for execution: {}'
                .format(execution_id)
            )

        self.logger_method(
            'debug',
            'Got status: "{0}" for execution ID: {1}',
            execution_status,
            execution_id
        )

        if execution_status in self._success_statuses:
            self.logger_method(
                'debug',
                'Execution {} succeeded !',
                execution_id
            )

            return True
        elif execution_status in self._failure_statuses:
            raise RuntimeError(
                'Execution {} failed ! Please check logs to get details.'
                .format(execution_id)
            )

        return False

    def run(self, execution_id):
        start_time = time.time()

        while time.time() <= start_time + self._timeout:
            if not self._check_execution_status(execution_id):
                self.logger_method(
                    'debug',
                    'Waiting {} seconds for next attempt '
                    'of execution status checking...',
                    self._interval
                )

                time.sleep(self._interval)
            else:
                return True

        self.logger_method(
            'error',
            'Execution {} status checking timed out !',
            execution_id
        )

        return False


class ExecutionRunner(object):

    WORKFLOW_EXECUTE_OPERATION = 'execute_operation'

    def __init__(self, logger_method, rest_client, **kwargs):
        self.logger_method = logger_method
        self.rest_client = rest_client
        self.poller = ExecutionStatusPoller(
            logger_method,
            rest_client,
            **kwargs
        )

    def _start_execution(self,
                         deployment_id,
                         workflow_id,
                         operation_name,
                         node_instance_ids,
                         operation_inputs,
                         force=True):

        parameters = {
            'node_instance_ids': node_instance_ids,
            'operation': operation_name,
            'operation_kwargs': operation_inputs,
            'allow_kwargs_override': True

        }

        execution = self.rest_client.executions.start(
            deployment_id,
            workflow_id,
            parameters=parameters,
            allow_custom_parameters=True,
            force=force
        )

        return execution.id

    def _check_execution_status(self, execution_id):
        return self.poller.run(execution_id)

    def _get_runtime_properties(self, node_instance_id):
        node_instance_response = self.rest_client.node_instances.get(
            node_instance_id
        )

        return node_instance_response.runtime_properties

    def run(self,
            deployment_id,
            node_instance_id,
            operation_name,
            operation_inputs,
            **kwargs):

        workflow_id = kwargs.get(
            'workflow_id',
            self.WORKFLOW_EXECUTE_OPERATION
        )

        self.logger_method(
            'debug',
            'Running workflow {0} for deployment {1} with inputs {2}',
            workflow_id,
            deployment_id,
            operation_inputs
        )

        execution_id = self._start_execution(
            deployment_id,
            workflow_id,
            operation_name,
            [node_instance_id],
            operation_inputs
        )

        self.logger_method('debug', 'Got execution ID: {}', execution_id)

        return execution_id

    def wait_for_result(self, execution_id, node_instance_id):
        if self._check_execution_status(execution_id):
            self.logger_method(
                'debug',
                'Getting runtime_properties for node instance: {}',
                node_instance_id
            )

            return self._get_runtime_properties(node_instance_id)

        return {}

    def run_and_wait_for_result(self,
                                deployment_id,
                                node_instance_id,
                                operation_name,
                                operation_inputs,
                                **kwargs):

        execution_id = self.run(
            deployment_id,
            node_instance_id,
            operation_name,
            operation_inputs,
            **kwargs
        )

        return self.wait_for_result(execution_id, node_instance_id)

