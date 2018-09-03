from cloudify import manager
from cloudify.decorators import workflow
from resource_management_sdk import (
    MODES,
    DEFAULT_MODE,
    Engine,
)

from . import get_profile


@workflow
def calculate_resources_availability(ctx, mode=DEFAULT_MODE, **kwargs):
    rest_client = manager.get_rest_client()
    engine = Engine(ctx, rest_client)
    engine.run(MODES[mode])


@workflow
def check_resources_availability(ctx,
                                 project_id,
                                 profile_name=None,
                                 profile_str=None,
                                 mode=DEFAULT_MODE,
                                 **kwargs):

    rest_client = manager.get_rest_client()
    engine = Engine(ctx, rest_client)
    profile = get_profile(rest_client, profile_name, profile_str)

    engine.run(MODES[mode])
    ctx.logger.info(
        'Calculating resources availability finished.\n'
        'Validation of resource profile started ...'
    )
    engine.validate_profile(project_id, profile)


@workflow
def execute_conditionally(ctx,
                          execution_dict,
                          project_id,
                          profile_name=None,
                          profile_str=None,
                          mode=DEFAULT_MODE,
                          **kwargs):

    rest_client = manager.get_rest_client()
    engine = Engine(ctx, rest_client)
    profile = get_profile(rest_client, profile_name, profile_str)

    engine.run(MODES[mode])
    ctx.logger.info(
        'Calculating resources availability finished.\n'
        'Validation of resource profile started ...'
    )

    engine.validate_profile(project_id, profile)
    ctx.logger.info(
        'Resource profile validated successfully - starting execution {}'
        .format(execution_dict)
    )

    execution = rest_client.executions.start(**execution_dict)
    ctx.logger.info(
        'Execution {} started successfully !'.format(execution)
    )
