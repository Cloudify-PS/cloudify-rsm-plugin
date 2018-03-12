from cloudify.decorators import workflow
from cloudify import manager


from resource_management_sdk import (
    Engine,
    get_handlers,
)


@workflow
def check_resources_availability(ctx, **kwargs):
    engine = Engine(
        ctx.logger,
        manager.get_rest_client(),
        get_handlers()
    )

    engine.run(ctx, 'cfy_test_project', '')
