from .constants import (
    NODE_TYPE_PROJECT,
    NODE_TYPE_QUOTA,
    NODE_TYPE_USAGE,
    NODE_TYPE_RESULT,
    SYSTEM_NAME_OPENSTACK
)


class Handler(object):
    """Base class for handler used for project instances - can read all
    instances from project deployment and add it into
    ResourceManagementContext

    Attributes:
        logger: logger instance"""

    def __init__(self, logger):
        """Class constructor.

        Args:
            logger: internal loger for use in calls."""
        self.logger = logger

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Args:
            rsm_ctx: instance for check.

        Returns:
            False, overwrited in inherit types"""
        return False

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
        pass


class NoopHandler(Handler):
    """Hadler for handle unsupported instances types and log such

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be None.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return not rsm_ctx.instance.type

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Write to log message that type is unsupported.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
        rsm_ctx.log(
            'info',
            'Node instance has type with is not supported by '
            'Resource Management Plugin. Skipping'
        )


class ProjectHandler(Handler):
    """Handler for resolve project on 'rsm_ctx' context.

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_PROJECT.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return rsm_ctx.instance.type == NODE_TYPE_PROJECT

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Run resolve project on 'rsm_ctx'.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
        rsm_ctx.log('info', 'Processing of project started')
        rsm_ctx.resolve_project()


class _RuntimePropertyHandlerBase(Handler):
    """Base class for handler based on process values from runtime properties
    and run set_value on 'rsm_ctx' context.

    Attributes:
        logger: logger instance"""
    VALUE_TYPE_QUOTA = 'quota'
    VALUE_TYPE_USAGE = 'usage'

    @staticmethod
    def _is_number(value):
        """Value can be converted to float"""
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_iterable(value):
        """Value is list or tuple"""
        return isinstance(value, list) or isinstance(value, tuple)

    @staticmethod
    def _is_dict(value):
        """Value is dictionary"""
        return isinstance(value, dict)

    @staticmethod
    def _set_value(rsm_ctx, value, value_type, resource_name=None):
        """Set value by resource managment context instance"""
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
        """Process dictionary value"""
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
        """Process number value"""
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
        """Process runtime properties"""
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
            'debug',
            'Not supported {1} type "{0}" of runtime property "{2}"',
            repr(runtime_property_value),
            value_type,
            runtime_property_name
        )


class SimpleQuotaHandler(_RuntimePropertyHandlerBase):
    """Gathers quota value from instance runtime_properties

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_QUOTA.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return rsm_ctx.instance.type == NODE_TYPE_QUOTA

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Process quota state from properties and run set_value on 'rsm_ctx'.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
        self._process_runtime_properties(
            rsm_ctx,
            rsm_ctx.instance.runtime_properties,
            self.VALUE_TYPE_QUOTA
        )


class SimpleUsageHandler(_RuntimePropertyHandlerBase):
    """Gathers usage value from instance runtime_properties (used in
    'simple' mode)

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_USAGE.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Process state from properties and run set_value on 'rsm_ctx'.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
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
    """Starts ('list') operartion execution for usage value gathering (used in
    'parallel' mode)

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_USAGE.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Run execution on 'rsm_ctx'.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
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
    """Checks if ('list') operartion execution started by
    'ExecutionStartUsageHandler' has ended. If yes gathers result as usage
    value (used in 'parallel' mode)

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_USAGE.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Process state from properties and run set_value on 'rsm_ctx'.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
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
    """Gathers quota value from instance runtime_properties and do necessary
    resources names translation for Openstack

    Attributes:
        logger: logger instance"""

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
        """Key in SUPPRESS list"""
        return key in self.SUPPRESS

    def _translate(self, key):
        """Translate key by translate dict"""
        return self.TRANSLATE.get(key, key)

    def _process_dict_value(self,
                            rsm_ctx,
                            value_type,
                            runtime_property_name,
                            runtime_property_value):
        """Process dictionary value"""
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
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_QUOTA and SYSTEM_NAME_OPENSTACK in
        'system_name'.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return super(OpenstackQuotaHandler, self).can_handle(rsm_ctx) and \
            SYSTEM_NAME_OPENSTACK in rsm_ctx.instance.system_name


class ResultHandler(Handler):
    """Used for 'result' instances - dumps current 'ResourceManagementContext'
    as runtime_property

    Attributes:
        logger: logger instance"""

    def can_handle(self, rsm_ctx):
        """Check support 'rsm_ctx' type by handler.

        Instance should be NODE_TYPE_RESULT.

        Args:
            rsm_ctx: instance for check.

        Returns:
            True if Handler is able to process given type of 'rsm_ctx'"""
        return rsm_ctx.instance.type == NODE_TYPE_RESULT

    def handle(self, rsm_ctx):
        """Logic which should be executed for given 'rsm_ctx'.

        Dump state to runtime properties.

        Args:
            rsm_ctx: instance for handle.

        Returns:
            None"""
        rsm_ctx.log(
            'info',
            'Dumping gathered data to runtime_properties of {} node instance',
            rsm_ctx.instance.id
        )

        rsm_ctx.add_result_instance_id()
        rsm_ctx.set_runtime_properties({
            'data': rsm_ctx.dump()
        })
