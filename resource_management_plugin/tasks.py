from cloudify import manager
from cloudify.decorators import workflow
from resource_management_sdk import (
    DEFAULT_HANDLER_CHAIN,
    Engine,
)

from . import get_profile


@workflow
def check_resources_availability(ctx,
                                 project_id,
                                 profile_name=None,
                                 profile_str=None,
                                 **kwargs):
    rest_client = manager.get_rest_client()
    engine = Engine(ctx, rest_client)
    profile = get_profile(rest_client, profile_name, profile_str)

    engine.run(DEFAULT_HANDLER_CHAIN)
    engine.validate_profile(project_id, profile)
