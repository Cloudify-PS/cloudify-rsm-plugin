from .constants import (
    NODE_TYPE_PROJECT,
    NODE_TYPE_QUOTA,
    NODE_TYPE_USAGE,
    NODE_TYPE_RESULT,
    SYSTEM_NAME_OPENSTACK
)


class Handler(object):

    def __init__(self, logger):
        self.logger = logger

    def can_handle(self, rsm_ctx):
        return False

    def handle(self, rsm_ctx):
        pass


class NoopHandler(Handler):

    def can_handle(self, rsm_ctx):
        return not rsm_ctx.instance.type

    def handle(self, rsm_ctx):
        rsm_ctx.log(
            'info',
            'Node instance has type with is not supported by '
            'Resource Management Plugin. Skipping'
        )


class ProjectHandler(Handler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_PROJECT

    def handle(self, rsm_ctx):
        rsm_ctx.log('info', 'Processing of project started')
        rsm_ctx.resolve_project()


class _RuntimePropertyHandlerBase(Handler):

    VALUE_TYPE_QUOTA = 'quota'
    VALUE_TYPE_USAGE = 'usage'

    @staticmethod
    def _is_number(value):
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_iterable(value):
        return isinstance(value, list) or isinstance(value, tuple)

    @staticmethod
    def _is_dict(value):
        return isinstance(value, dict)

    @staticmethod
    def _set_value(rsm_ctx, value, value_type, resource_name=None):
        value_dict = {value_type: value}

        if resource_name:
            value_dict['resource_name'] = resource_name

        rsm_ctx.log('debug', 'Setting {}', value_dict)
        rsm_ctx.set_value(**value_dict)

    def _process_dict_value(self,
                            rsm_ctx,
                            value_type,
                            runtime_property_name,
                            runtime_property_value):
        rsm_ctx.log(
            'debug',
            'Found {0} dict value defined in "{1}" runtime property '
            '- but resource name has been not specified. '
            'Trying to set values based of dict value keys',
            value_type,
            runtime_property_name
        )

        for key, value in runtime_property_value.iteritems():
            if isinstance(key, basestring) and self._is_number(value):
                self._set_value(rsm_ctx, value, value_type, key)

    def _process_number_value(self,
                              rsm_ctx,
                              value_type,
                              runtime_property_name,
                              runtime_property_value,
                              resource_name):

        rsm_ctx.log(
            'debug',
            'Found {0} numerical value defined in "{1}" '
            'runtime property (for resource: {2})',
            value_type,
            runtime_property_name,
            resource_name
        )

        self._set_value(rsm_ctx, runtime_property_value, value_type)

    def _process_runtime_properties(self,
                                    rsm_ctx,
                                    runtime_properties,
                                    value_type):
        resource_name = rsm_ctx.instance.resource_name
        runtime_property_name = rsm_ctx.instance.runtime_property_name
        runtime_property_value = runtime_properties.get(
            runtime_property_name,
            None
        )

        if runtime_property_value is None:
            rsm_ctx.log(
                'warn',
                'Runtime property "{0}" not found in runtime properties: {1}',
                runtime_property_name,
                runtime_properties
            )

            return

        if self._is_number(runtime_property_value) and resource_name:
            self._process_number_value(
                rsm_ctx,
                value_type,
                runtime_property_name,
                runtime_property_value,
                resource_name
            )

            return

        elif self._is_iterable(runtime_property_value):
            self._process_number_value(
                rsm_ctx,
                value_type,
                runtime_property_name,
                len(runtime_property_value),
                resource_name
            )

            return
        elif self._is_dict(runtime_property_value):
            nested_value = runtime_property_value.get(
                resource_name,
                None
            )

            if self._is_number(nested_value):
                self._process_number_value(
                    rsm_ctx,
                    value_type,
                    runtime_property_name,
                    nested_value,
                    resource_name
                )
            else:
                self._process_dict_value(
                    rsm_ctx,
                    value_type,
                    runtime_property_name,
                    runtime_property_value
                )

            return

        rsm_ctx.log(
            'debug'
            'Not supported {1} type "{0}" of runtime property "{2}"',
            type(runtime_property_value),
            value_type,
            runtime_property_name
        )


class SimpleQuotaHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_QUOTA

    def handle(self, rsm_ctx):
        self._process_runtime_properties(
            rsm_ctx,
            rsm_ctx.instance.runtime_properties,
            self.VALUE_TYPE_QUOTA
        )


class SimpleUsageHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        rsm_ctx.log('info', 'Executing "list" operation for get usage ...')

        runtime_properties = rsm_ctx.run_execution()
        rsm_ctx.log(
            'info',
            'Got {} runtime_properties after execution',
            runtime_properties.keys()
        )

        self._process_runtime_properties(
            rsm_ctx,
            runtime_properties,
            self.VALUE_TYPE_USAGE
        )


class ExecutionStartUsageHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        rsm_ctx.log(
            'info',
            'Starting executing for "list" operation for get usage ...'
        )

        execution_id = rsm_ctx.run_execution(wait=False)
        rsm_ctx.log(
            'info',
            'Execution started with ID: {} ...'.format(execution_id)
        )


class ExecutionResultUsageHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        runtime_properties = rsm_ctx.get_execution_result()

        rsm_ctx.log(
            'info',
            'Got {} runtime_properties after execution',
            runtime_properties.keys()
        )

        self._process_runtime_properties(
            rsm_ctx,
            runtime_properties,
            self.VALUE_TYPE_USAGE
        )


class OpenstackQuotaHandler(SimpleQuotaHandler):

    OPENSTACK_COMPONENT_NAMES = ['cinder', 'neutron', 'nova']

    # items from nova networking - currently not supported
    SUPPRESS = ['floating_ips', 'security_groups']

    TRANSLATE = {
        'volumes': 'volume',
        'key_pairs': 'keypair',
        'floatingip': 'floating_ip',
        'server_groups': 'server_group',
        'instances': 'server'
    }

    def _suppress(self, key):
        return key in self.SUPPRESS

    def _translate(self, key):
        return self.TRANSLATE.get(key, key)

    def _process_dict_value(self,
                            rsm_ctx,
                            value_type,
                            runtime_property_name,
                            runtime_property_value):
        rsm_ctx.log(
            'debug',
            'Found openstack quota dict value defined in "{1}" runtime '
            'property. Looking for quota for each of openstack components.',
            value_type,
            runtime_property_name
        )

        for component, component_values in runtime_property_value.iteritems():
            if isinstance(component, basestring) \
                    and component in self.OPENSTACK_COMPONENT_NAMES:

                rsm_ctx.log('debug', 'Found quota for: {0}', component)

                for key, value in component_values.iteritems():
                    if isinstance(key, basestring) and \
                            not self._suppress(key) and \
                            self._is_number(value):

                        self._set_value(
                            rsm_ctx,
                            value,
                            value_type,
                            self._translate(key)
                        )

    def can_handle(self, rsm_ctx):
        return super(OpenstackQuotaHandler, self).can_handle(rsm_ctx) and \
               SYSTEM_NAME_OPENSTACK in rsm_ctx.instance.system_name


class ResultHandler(Handler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_RESULT

    def handle(self, rsm_ctx):
        rsm_ctx.log(
            'info',
            'Dumping gathered data to runtime_properties of {} node instance',
            rsm_ctx.instance.id
        )

        rsm_ctx.add_result_instance_id()
        rsm_ctx.set_runtime_properties({
            'data': rsm_ctx.dump()
        })
