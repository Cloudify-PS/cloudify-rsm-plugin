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


class QuotaHandler(Handler):

    def can_handle(self, rsm_ctx):
        return False

    def handle(self, rsm_ctx):
        super(QuotaHandler, self).handle(rsm_ctx)


class UsageHandler(Handler):

    def can_handle(self, rsm_ctx):
        return False

    def handle(self, rsm_ctx):
        super(UsageHandler, self).handle(rsm_ctx)


class NoopHandler(Handler):

    def can_handle(self, rsm_ctx):
        return not rsm_ctx.instance.type

    def handle(self, rsm_ctx):
        super(NoopHandler, self).handle(rsm_ctx)
        self.logger.info(
            'Node instance {} has type with is not supported by '
            'Resource Management Plugin. Skipping'
            .format(rsm_ctx.instance.id)
        )


class ProjectHandler(Handler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_PROJECT

    def handle(self, rsm_ctx):
        super(ProjectHandler, self).handle(rsm_ctx)
        self.logger.info('ProjectHandler.handle')

        rsm_ctx.resolve_project()


class GlobalQuotaHandler(QuotaHandler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_PROJECT and \
               rsm_ctx.instance.scope == SCOPE_GLOBAL

    def handle(self, rsm_ctx):
        super(GlobalQuotaHandler, self).handle(rsm_ctx)
        self.logger.info('GlobalQuotaHandler.handle')


class ProjectQuotaHandler(QuotaHandler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_QUOTA and \
               rsm_ctx.instance.scope == SCOPE_PROJECT

    def handle(self, rsm_ctx):
        super(ProjectQuotaHandler, self).handle(rsm_ctx)
        self.logger.info('ProjectQuotaHandler.handle')


class GlobalUsageHandler(UsageHandler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_USAGE and \
               rsm_ctx.instance.scope == SCOPE_GLOBAL

    def handle(self, rsm_ctx):
        super(GlobalUsageHandler, self).handle(rsm_ctx)
        self.logger.info('GlobalUsageHandler.handle')

        rsm_ctx.set_result(usage=15)


class ProjectUsageHandler(UsageHandler):

    def can_handle(self, rsm_ctx):
        return rsm_ctx.instance.type == NODE_TYPE_USAGE and \
               rsm_ctx.instance.scope == SCOPE_PROJECT

    def handle(self, rsm_ctx):
        super(ProjectUsageHandler, self).handle(rsm_ctx)
        self.logger.info('ProjectUsageHandler.handle')

        rsm_ctx.set_result(usage=8)
