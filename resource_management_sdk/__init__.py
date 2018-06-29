from cloudify.exceptions import NonRecoverableError

from context import ResourceManagementContext
from handle import *
from profile import ResourcesProfile

SIMPLE_HANDLER_CHAIN = [
    [
        NoopHandler,
        ProjectHandler,
        OpenstackQuotaHandler,
        SimpleQuotaHandler,
        SimpleUsageHandler
    ]
]

PARALLEL_EXECUTIONS_HANDLER_CHAIN = [
    [
        ProjectHandler
    ],
    [
        ExecutionStartUsageHandler
    ],
    [
        OpenstackQuotaHandler,
        SimpleQuotaHandler
    ],
    [
        ExecutionResultUsageHandler
    ]
]

SIMPLE_MODE_KEYWORD = 'simple'
PARALLEL_MODE_KEYWORD = 'parallel'
DEFAULT_MODE = SIMPLE_MODE_KEYWORD

MODES = {
    SIMPLE_MODE_KEYWORD: SIMPLE_HANDLER_CHAIN,
    PARALLEL_MODE_KEYWORD: PARALLEL_EXECUTIONS_HANDLER_CHAIN
}


class Engine(object):

    def __init__(self, ctx, rest_client):
        self.logger = ctx.logger
        self.rest_client = rest_client
        self.rsm_ctx = ResourceManagementContext(ctx, self.rest_client)

    def _get_profile(self, profile_str):
        return ResourcesProfile.get_profile_from_string(
            self.logger,
            profile_str
        )

    def _validate_profile(self, rsm_ctx, profile, project_id):
        self.logger.info('Validating profile: {}\n'.format(profile))
        return profile.validate(rsm_ctx, project_id)

    def _report_data(self):
        self.logger.info(
            '\nCalculated resources availabilities: \n{}'
            .format(
                ''.join(
                    '* {0}: {1}\n'.format(k, v)
                    for k, v
                    in self.rsm_ctx.collected_data.iteritems()
                )
            )
        )

    def _report_result(self, errors):
        if errors:
            errors_str = ''.join('* {}\n'.format(e.message) for e in errors)
            message = '\nResource availability issues found ' \
                      'during profile validation: \n{}'.format(errors_str)

            self.logger.error(message)
            raise NonRecoverableError(message)

        else:
            self.logger.info(
                'Profile validation ended successfully - no issues found !'
            )

    def _run(self, handler_chain, report=True):
        self.rsm_ctx.reset()
        handlers = [handler_cls(self.logger) for handler_cls in handler_chain]

        while True:
            for handler in handlers:
                if handler.can_handle(self.rsm_ctx):
                    handler.handle(self.rsm_ctx)
                    break

            if not self.rsm_ctx.next_instance():
                break

        if report:
            self._report_data()

    def run(self, handler_chains, report=True):
        for handler_chain in handler_chains:
            if type(handler_chain) not in set([list, tuple]):
                handler_chain = [handler_chain]

            self.logger.info(
                '\n\n\n---------------------------\n\n'
                'Running rsm-plugin engine for handlers chain: {}'
                '\n\n---------------------------\n\n\n'
                .format(handler_chain)
            )
            self._run(handler_chain, report)

    def validate_profile(self, project_id, profile_str, report=True):
        profile = self._get_profile(profile_str)

        errors = self._validate_profile(
            self.rsm_ctx,
            profile,
            project_id
        )

        if report:
            self._report_result(errors)

        return errors

