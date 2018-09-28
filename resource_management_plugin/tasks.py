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
    """Calculate current resource availability.

    This workflow will gather information about usages and quotas defined by
    deployment and then based on these values will calculate availabilities
    for found types of resources.

    Result will be shown in outputs logs and can by dumped by
    'cloudify.nodes.resource_management.Result' node template.

    Args:
        mode: flag decides how workflow will run executions to gather required
            values (e.g. 'list' operation for usage). It can be 'simple'
            (default) or 'parallel'.

    Returns:
        None, In case of success workflow execution will finish normally."""
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
    """Get resource availability and validate.

    This workflow will calculate resource availabilities like
    'calculate_resources_availability' and then it can check if there is enough
    resources for given types in the system.

    Resources requirements are described by 'resource profile'.

    Args:
        project_id: identifier of project, for which resource profile should be
            validated
        profile_name: Name of secret from secret store which is containing
            resource profiles definition as "JSON string" (in case when
            'profile_str' is not specified; default method of providing
            resource profile)
        profile_str: string containing resource profile definition (in case
            when 'profile_name' is not specified). It may be used when you
            would like to pass profile definiction directly without using
            secret store.
        mode: flag decides how workflow will run executions to gather required
            values (e.g. 'list' operation for usage). It can be 'simple'
            (default) or 'parallel'.

    Returns:
        None, In case of success workflow execution will finish normally.
        Calculations will be available also is output logs and in
        'runtime_properties' of 'cloudify.nodes.resource_management.Result'
        node template.

    Raises:
        NonRecoverableError: In case of failure exception will be raised and
        workflow execution will be in 'failed' state."""

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
    """Run workflow conditionally to avaible resources.

    This workflow will validate resource profile the same way like
    'check_resources_availability. Then in case of validation success it will
    start some execution described by input parameter. Purpose of this
    workflow is to provide possibility of running some execution only when
    given amount of resources is available in the system.

    Args:
        execution_dict: dictionaty describes execution. Uses the same format
            like Cloudify executions REST API:
                deployment_id: mandatory
                workflow_id: mandatory
                allow_custom_parameters: optional
                parameters: optional
                force: optional
        project_id: identifier of project, for which resource profile should be
            validated
        profile_name: Name of secret from secret store which is containing
            resource profiles definition as 'JSON string' (in case when
            'profile_str' is not specified; default method of providing
            resource profile).
        profile_str: string containing resource profile definition (in
            case when profile_name is not specified). It may be used when you
            would like to pass profile definiction directly without
            using secret store.
        mode: flag decides how workflow will run executions to gather required
            values (e.g. 'list' operation for usage). It can be 'simple'
            (default) or 'parallel'.

    Returns:
        None, In case of success workflow execution will finish normally."""

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
