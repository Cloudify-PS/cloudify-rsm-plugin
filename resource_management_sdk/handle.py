from .constants import (
    NODE_TYPE_PROJECT,
    NODE_TYPE_QUOTA,
    NODE_TYPE_USAGE,
    SCOPE_GLOBAL,
    SCOPE_PROJECT
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
        self.logger.info(
            'Node instance {} has type with is not supported by '
            'Resource Management Plugin. Skipping'
            .format(rsm_ctx.instance.id)
        )


class ProjectHandler(Handler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_PROJECT

    def handle(self, rsm_ctx):
        self.logger.info('ProjectHandler.handle')

        rsm_ctx.resolve_project()


class _RuntimePropertyHandlerBase(Handler):

    @staticmethod
    def _get_resource_name(rsm_ctx):
        return rsm_ctx.instance.resource_name

    @staticmethod
    def _get_runtime_property_name(rsm_ctx):
        return rsm_ctx.instance.runtime_property_name

    @staticmethod
    def _get_runtime_property_value(rsm_ctx):
        return rsm_ctx.instance.runtime_property_value

    def can_handle(self, rsm_ctx):
        return self._get_runtime_property_name(rsm_ctx) \
               and rsm_ctx.instance.type == NODE_TYPE_QUOTA  # TODO remove ?


class SingleNumberHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        result = super(SingleNumberHandler, self).can_handle(rsm_ctx) and \
                 self._get_resource_name(rsm_ctx)

        try:
            float(self._get_runtime_property_value(rsm_ctx))
        except (TypeError, ValueError):
            result = False

        return result

    def handle(self, rsm_ctx):
        resource_name = self._get_resource_name(rsm_ctx)
        value = self._get_runtime_property_value(rsm_ctx)

        self.logger.info(
            'SingleNumberHandler - setting value {0} for {1}'
            .format(value, resource_name)
        )

        rsm_ctx.set_result(quota=value, resource_name=resource_name)


class SingleDictHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        return super(SingleDictHandler, self).can_handle(rsm_ctx) \
            and self._get_resource_name(rsm_ctx) \
            and isinstance(self._get_runtime_property_value(rsm_ctx), dict)

    def handle(self, rsm_ctx):
        resource_name = self._get_resource_name(rsm_ctx)
        value = self._get_runtime_property_value(rsm_ctx) \
            .get(resource_name, None)

        if value:
            self.logger.info(
                'SingleDictHandler - setting value {0} for {1}'
                .format(value, resource_name)
            )

            rsm_ctx.set_result(quota=value, resource_name=resource_name)
        else:
            self.logger.warn(
                'SingleDictHandler - resource_name has been defined to {} '
                'but not found in dict runtime property'
                .format(resource_name)
            )


class MultipleDictHandler(_RuntimePropertyHandlerBase):

    def can_handle(self, rsm_ctx):
        return super(MultipleDictHandler, self).can_handle(rsm_ctx) \
           and not self._get_resource_name(rsm_ctx) \
           and isinstance(self._get_runtime_property_value(rsm_ctx), dict)

    def handle(self, rsm_ctx):
        runtime_property = self._get_runtime_property_value(rsm_ctx)

        for resource_name, value in runtime_property.iteritems():
            self.logger.info(
                'MultipleDictHandler - setting value {0} for {1}'
                .format(value, resource_name)
            )

            rsm_ctx.set_result(quota=value, resource_name=resource_name)
