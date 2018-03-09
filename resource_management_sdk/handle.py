from .constants import (
    NODE_TYPE_PROJECT,
    NODE_TYPE_QUOTA,
    NODE_TYPE_USAGE
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
        rsm_ctx.log_message(
            'info',
            'Node instance has type with is not supported by '
            'Resource Management Plugin. Skipping'
        )


class ProjectHandler(Handler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_PROJECT

    def handle(self, rsm_ctx):
        rsm_ctx.log_message('info', 'Processing of project started')
        rsm_ctx.resolve_project()


class _RuntimePropertyHandlerBase(Handler):

    VALUE_TYPE_QUOTA = 'quota'
    VALUE_TYPE_USAGE = 'usage'

    def _set_value(self, rsm_ctx, value, value_type, resource_name=None):
        value_dict = {value_type: value}

        if resource_name:
            value_dict['resource_name'] = resource_name

        rsm_ctx.log_message('debug', 'Setting {}', value_dict)
        rsm_ctx.set_value(**value_dict)

    def _process_runtime_properties(self,
                                    rsm_ctx,
                                    runtime_properties,
                                    value_type):

        def _is_number(value):
            try:
                float(value)
                return True
            except (TypeError, ValueError):
                return False

        def _is_dict(value):
            return isinstance(value, dict)

        resource_name = rsm_ctx.instance.resource_name
        runtime_property_name = rsm_ctx.instance.runtime_property_name
        runtime_property_value = runtime_properties.get(
            runtime_property_name,
            None
        )

        if not runtime_property_value:
            rsm_ctx.log_message(
                'warn',
                'Runtime property "{0}" not found in runtime properties: {1}',
                runtime_property_name,
                runtime_properties
            )

            return

        if _is_number(runtime_property_value) and resource_name:
            rsm_ctx.log_message(
                'debug',
                'Found {0} numerical value defined in "{1}" '
                'runtime property (for resource: {2})',
                value_type,
                runtime_property_name,
                resource_name
            )

            self._set_value(rsm_ctx, runtime_property_value, value_type)

            return

        elif _is_dict(runtime_property_value):
            nested_value = runtime_property_value.get(
                resource_name,
                None
            )

            if _is_number(nested_value):
                rsm_ctx.log_message(
                    'debug',
                    'Found {0} dict value defined in "{1}" '
                    'runtime property (for resource: {2})',
                    value_type,
                    runtime_property_name,
                    resource_name
                )

                self._set_value(rsm_ctx, nested_value, value_type)
            else:
                rsm_ctx.log_message(
                    'debug',
                    'Found {0} dict value defined in "{1}" runtime property '
                    '- but resource name has been not specified. '
                    'Trying to set values based of dict value keys',
                    value_type,
                    runtime_property_name,
                    resource_name
                )

                for key, value in runtime_property_value.iteritems():
                    if isinstance(key, str) and _is_number(value):
                        self._set_value(rsm_ctx, value, value_type, key)

            return

        rsm_ctx.log_message(
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

    # TODO
    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_USAGE

    def handle(self, rsm_ctx):
        rsm_ctx.log_message('info', '[TEST] USAGE HANDLER')
        rsm_ctx.set_value(usage=1)

    class RuntimePropertyQuotaHandler(_RuntimePropertyHandlerBase):
        def can_handle(self, rsm_ctx):
            return rsm_ctx.instance.type == NODE_TYPE_QUOTA

        def handle(self, rsm_ctx):
            self._process_runtime_properties(
                rsm_ctx,
                rsm_ctx.instance.runtime_properties,
                self.VALUE_TYPE_QUOTA
            )


class OpenstackQuotaHandler(_RuntimePropertyHandlerBase):
    pass


class OpenstackUsageHandler(_RuntimePropertyHandlerBase):
    pass
