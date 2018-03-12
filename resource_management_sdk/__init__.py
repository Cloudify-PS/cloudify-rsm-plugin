from context import ResourceManagementContext
from handle import (
    NoopHandler,
    ProjectHandler,
    SimpleQuotaHandler,
    SimpleUsageHandler,
    OpenstackQuotaHandler
)
from profile import ResourcesProfile

DEFAULT_HANDLER_CHAIN = (
    NoopHandler,
    ProjectHandler,
    OpenstackQuotaHandler,
    SimpleQuotaHandler,
    SimpleUsageHandler
)


class Engine(object):

    def __init__(self, logger, rest_client, handlers):
        self.logger = logger
        self.rest_client = rest_client
        self.handlers = [handler_cls(logger) for handler_cls in handlers]

    def _collect_data(self, rsm_ctx):
        while True:
            for handler in self.handlers:
                if handler.can_handle(rsm_ctx):
                    handler.handle(rsm_ctx)
                    break

            if not rsm_ctx.next_instance():
                break

    def _get_profile(self, profile_str):
        return ResourcesProfile.get_profile_from_string(self.logger, profile_str)

    def _validate_profile(self, rsm_ctx, profile, project_id, profile_str):
        self.logger.info('Validating profile: {}'.format(profile))
        return profile.validate(rsm_ctx, project_id)

    def _report_collected_data(self, rsm_ctx):
        self.logger.info(
            '\nCalculated resources availabilities: \n{}'
            .format(
                ''.join(
                    '* {0}: {1}\n'.format(k, v)
                    for k, v
                    in rsm_ctx.collected_data.iteritems()
                )
            )
        )

    def _report_result(self, errors):
        if errors:
            self.logger.error(
                '\nResource availability issues found '
                'during profile validation: \n{}'
                .format(
                    ''.join('* {}\n'.format(e.message) for e in errors)
                )
            )
        else:
            self.logger.info(
                'Profile validation ended successfully - no issues found !'
            )

    def run(self, ctx, project_id, profile_str):
        rsm_ctx = ResourceManagementContext(ctx, self.rest_client)
        profile = self._get_profile(profile_str)

        self._collect_data(rsm_ctx)
        self._report_collected_data(rsm_ctx)

        errors = self._validate_profile(
            rsm_ctx,
            profile,
            project_id,
            profile_str
        )
        self._report_result(errors)

        return errors


def get_handlers():
    return DEFAULT_HANDLER_CHAIN
