from cloudify import ctx
from cloudify.workflows import ctx as workflow_ctx
from cloudify.decorators import workflow

from cloudify import manager

import json


LIFECYCLE_OPERATION_RESOURCES_LIST = 'cloudify.interfaces.lifecycle.resources_list'


@workflow
def validate_profiles_workflow(profile,
           project_nodes,
           global_nodes,
           **kwargs):
    ctx = workflow_ctx

# For each node of the project nodes execute list operation
    run_operation_on_nodes(LIFECYCLE_OPERATION_RESOURCES_LIST, global_nodes, ctx)

# For each node of the global nodes execute list operations
    run_operation_on_nodes(LIFECYCLE_OPERATION_RESOURCES_LIST, project_nodes, ctx)


# check if there is sufficant resourecs in project Node
   # create merged resources from all project Node
   # compare to profile
   merge_node_resources_and_compare_to_profile(project_nodes,profile)

# To be implemented later
####################
# check if there is sufficant resourecs in global Node
   ## create merged resources from all project Nodes
   # compare to profile

#> function that mergers resources from list of nodes


#
# Implementation functions
#############
def run_operation_on_nodes(operation, nodes_list, ctx):
    sequence = graph.sequence()
    for node in ctx.nodes:
        if node.id in  nodes_list :   #if current node is in list of nodes
            for instance in  node.instances:
                ### Add operation to sequance



def merge_node_resources_and_compare_to_profile(nodes,profile):

    resource_pool = []

    for node in ctx.nodes:
        if node.id in  nodes_list :   #if current node is in list of nodes
          for instance in  node.instances:
              resource_pool = merger_resources(node.instances,resource_pool)

    available_resource_pool = calculate_available_resources(resource_pool)

    compare_pool_to_profile(available_resource_pool, profile)

def merger_resources(instance,resource_pool):
    ## merge and resources into the pool
return resource_pool

def compare_pool_to_profile(available_resource_pool, profile):

def calculate_available_resources(resource_pool)

    quota_pool = resource_pool['quota']
    allocated_pool = resource_pool['allocated']
    available_resource_pool = #Substract allocated_pool from quota_pool

return available_resource_pool
