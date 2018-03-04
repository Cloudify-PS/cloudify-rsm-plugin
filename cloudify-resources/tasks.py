from cloudify import ctx
from cloudify.workflows import ctx as workflow_ctx
from cloudify.decorators import workflow

from cloudify import manager

import json


LIFECYCLE_OPERATION_RESOURCES_LIST = 'cloudify.interfaces.lifecycle.resources_list'



@workflow
def validate_profiles_workflow(profiles,
           pool_nodes,
           **kwargs):

# For each node of the project nodes execute list operation

# For each node of the global nodes execute list operations

# check if there is sufficant resourecs in project Node
   # create merged resources from all project Node
   # compare to profile


####################
# check if there is sufficant resourecs in global Node
   ## create merged resources from all project Nodes
   # compare to profile

#> function that mergers resources from list of nodes
