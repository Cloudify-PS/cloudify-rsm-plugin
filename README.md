# Cloudify resource management plugin

## Overview

Resource management plugin has been designed as a utility which can be used by Cloudify blueprints 
in combination with different plugins to allow some basic resource management operations, like:
* Processing of qoutas and current usages for given kind of resources
* Calculating resources availabilities
* Validating resources requirements
* Running of execution only in case if resources requirements are met

Resource management plugin is independent from infrastructure management - 
it can only manage information about usages, quotas etc. but it cannot obtain such information by itself.
For this purpose some infrastructure management plugin should be used (e.g. cloudify-openstack-plugin).

## Concepts

* **Resources**

    RSM plugin (as it name says) operates on resources.
    By *resource* we can mean each type of object existing in some computer system, for which we can calculate *number of existing objects* (***usage***) and *limit of possible existing objects* (***quota***).
    RSM plugin uses these values to calculate ***availability*** - number of objects which we can create in given computer system.
    Then value of *availability* is used to take proper decisions.
    
* **Plugin**

    Plugin main features are:
    * Processing of qoutas and current usages for given kind of resources
    * Calculating resources availabilities
    * Validating resources requirements
    * Running of execution only in case if resources requirements are met
    
    Plugin needs blueprint(s) prepared in specific manner (described later) and provides set of ***workflows***. They use blueprint(s) deployment(s) to execute given operation.
    Plugin also provides support for multitenancy (it can operate in scope of whole system or single tenant / project).
    
* **Node types**

    Plugin exposes few node types describing resources in its *plugin.yaml* file.
    These node types have no interfaces assigned - thery are like interfaces in object-oriented programming languages.
    You need to assign proper interfaces (from separate VIM / system / device plugin) to provide support for given operation execution (like: quota get and set, objects list / usage calcluation).
    It should be done in the blueprint.
    
* **Blueprints**

    Blueprint for RSM plugin is basically resources (quotas, usages) description.
    Plugin workflows are using deployment of such blueprint as "source of knowledge" about resources to do their operations.
   
* **Multitenancy**

    RSM plugin can calculate resource availabilities per project / tenant of in given system.
    
    There are two kinds of blueprints:
    
    * ***global blueprint*** - describing system-wide resources and containing references to project blueprints / deployments.
    * ***project blueprint***  -  describing resources for single project / tenant
    
    When you will run workflow for global blueprint deployment plugin will find references to project blueprints and include them as project resources.
    When you will run workflow for deployment of blueprint with no references to projects, it will be treated as global (system-wide).
    
* **Resource identifiers**

    Each resource type in *cloudify-rsm-plugin* is identified by:
    
    * **system name** - name of system managing this resource. It can be e.g. *openstack* or *aws*. 
      It can be also name of given instance of this system e.g. *openstack_rackspace*. 
      Systems may be not only Virtual Infrastructure Managers but also single devices for which resource management plugin can be used e.g. *n7k*.
      In general it is identifier of any entity which is using resources which will be checked by RSM plugin.
      
    * **resource name** - identifier of resource (type of object in some system identified by **system name**). For example - for openstack it may be *security_group* or *flavor* or ... 
     
    * **scope** - either *project* or *global*. It specifies if this resource should be analysed is scope of whole system (*global*) or single tenant / project (*project*).
     
    * **project_id** - identifier of project / tenant in case of *scope=project*. Otherwise set to *global*.

* **Resource profile**

    One of RSM plugin features is *validation of resources requirements*. These requirements are described by object called ***resource profile***.
    Profile contains amounts of required types of resources per system and project.

## Node types

* **cloudify.nodes.resource_management.Usage**

    Node type represents usage for single resource.
    You need to implement ***list*** operation for ***cloudify.interfaces.operations***.
    This operation should return (set as *runtime_property*) list or number of objects for given resource type in system or project.
    ***List*** operation will be run by workflows.
    
    Properties:
    * ***system_name*** - identifier of system described in *Concepts / Resource identifiers* section
    * ***resource_name*** - identifier of resource described in *Concepts / Resource identifiers* section
    * ***scope*** - scope described in *Concepts / Resource identifiers* section
    * ***operation_inputs*** - dictionary containing input parameter required by *list* operations (it may be required by some VIM-plugins). 
    * ***runtime_property_name*** - name of *runtime_property* which will containg information about usage (number / list of objects) after execution of *list* operation
    
    Details you can find as descriptions in *plugin.yaml* file.

*  **cloudify.nodes.resource_management.Quota**

    Node type represents usage for single or multiple resource(s).
    You need to implement ***create*** lifecycle operation.
    This operation should return (set as *runtime_property*) quota value for given resource type in system or project.
    You may also implement ***update*** operation enables update of quota on given system.
    It is not used by plugin but may be useful.
          
    Properties:
    * ***system_name*** - identifier of system described in *Concepts / Resource identifiers* section
    * ***resource_name*** - identifier of resource described in *Concepts / Resource identifiers* section
    * ***scope*** - scope described in *Concepts / Resource identifiers* section
    * ***runtime_property_name*** - name of *runtime_property* which will containg information about quota
    
    Details you can find as descriptions in *plugin.yaml* file.

*  **cloudify.nodes.resource_management.Project**

    Reference to deployment of project blueprint. 
    To be used in main (global) blueprint. 

    Properties:
    * ***project_name*** - name of project
    * ***deployment_id*** - deployment ID for deployment created from project blueprint - it should be already installed

    Details you can find as descriptions in *plugin.yaml* file.

*  **cloudify.nodes.resource_management.Result**

    Node type with no properties, enables dumping of workflow execution result to runtime properties.

## Workflows

*  **calculate_resources_availability**

    This workflow will gather information about usages and quotas defined by deployment and then based on these values will calculate availabilities for found types of resources.
    Result will be shown in outputs logs and can by dumped by ***cloudify.nodes.resource_management.Result*** node template.

    Parameters:
    
    * ***mode*** - flag decides how workflow will run executions to gather required values (e.g. *list* operation for usage).
      It can be *simple* (default) or *parallel*.

*  **check_resources_availability**

    This workflow will calculate resource availabilities like ***calculate_resources_availability*** and then it can check if there is enough resources for given types in the system.
    Resources requirements are described by *resource profile*.
    In case of success workflow execution will finish normally.
    In case of failure ***NonRecoverableError*** will be raised and workflow execution will be in *failed* state.
    Calculations will be available also is output logs and in *runtime_properties* of ***cloudify.nodes.resource_management.Result*** node template.

    Parameters:
    
    * ***project_id*** - identifier of project, for which resource profile should be validated          
    * ***profile_name*** - Name of secret from secret store which is containing resource profiles
          definition as "JSON string" (in case when ***profile_str*** is not specified; default method of providing resource profile)
    * ***profile_str*** - string containing resource profile definition (in case when ***profile_name*** is not specified). It may be used when you would like to pass profile definiction directly without using secret store.
    * ***mode*** - flag decides how workflow will run executions to gather required values (e.g. *list* operation for usage).
      It can be *simple* (default) or *parallel*.

* **execute_conditionally**

    This workflow will validate resource profile the same way like ***check_resources_availability***.
    Then in case of validation success it will start some execution described by input parameter.
    Purpose of this workflow is to provide possibility of running some execution only when given amount of resources is available in the system.

    Parameters:
    
    * ***execution_dict*** - dictionaty describes execution. Uses the same format like Cloudify executions REST API:
        * *deployment_id* - mandatory
        * *workflow_id* - mandatory
        * *allow_custom_parameters* - optional
        * *parameters* - optional
        * *force* - optional
    * ***project_id*** - identifier of project, for which resource profile should be validated          
    * ***profile_name*** - Name of secret from secret store which is containing resource profiles
          definition as "JSON string" (in case when ***profile_str*** is not specified; default method of providing resource profile)
    * ***profile_str*** - string containing resource profile definition (in case when ***profile_name*** is not specified). It may be used when you would like to pass profile definiction directly without using secret store.
    * ***mode*** - flag decides how workflow will run executions to gather required values (e.g. *list* operation for usage).
      It can be *simple* (default) or *parallel*.
      
To see how to define ***resource profile*** please check ***openstack-resources-management*** example.
 
         
## Implementation

Plugin has been implemented as dedicated class (***Engine***) which operates on collection of ***Instance*** objects using ***Handler***s.
***Instance*** object is a representation of single *node instance* from the blueprint.
Subclasses of ***Handler*** class contains logic called to process specific kind of instance (*quota*, *usage*, etc.).
***Engine*** initialized with ***Handler*** list iterates through list of ***Instance*** object trying to find ***Handler*** suitable to this kind of ***Instance*** object.
If there is suitable ***Handler*** its logic will be executed for given ***Instance***.
***Engine*** and ***Handler*** classes are using ***ResourceManagementContext*** class as *knowledge base*.
Role of ***ResourceManagementContext*** is to store information about instances, already gathered quota / usage / availability data etc.

Code structure:

* **resource_management_plugin** - contains all ***CloudifyContext***-related stuff
    * **tasks** - contains entrypoint methods used by Cloudify workflows
* **resource_management_sdk**  - contains RSM plugin logic independent from ***CloudifyContext***
    * **constants** - declatarions of all constants used in plugin code  
    * **context** - ***ResourceManagementContext*** implementation 
    * **data** - all classes acting as data units used by ***Engine*** and ***ResourceManagementContext***
    * **execution** - logic related to running executions (e.g. for *list* operation) ald polling their results
    * **handler** - all ***Handler*** subclasses implementations
    * **instance** - stuff related to **Instance** objects (processing) 
    * **profile** - all things related to resource profile
    
Currently supported handlers:
* **ProjectHandler** - used for *project* instances - can read all instances from project deployment and add it into ***ResourceManagementContext***
* **SimpleQuotaHandler** - gathers quota value from instance runtime_properties 
* **SimpleUsageHandler** - gathers usage value from instance runtime_properties (used in *simple* mode)
* **ExecutionStartUsageHandler** - starts (*list*) operartion execution for usage value gathering (used in *parallel* mode)
* **ExecutionResultUsageHandler** - checks if (*list*) operartion execution started by ***ExecutionStartUsageHandler*** has ended. If yes gathers result as usage value (used in *parallel* mode)
* **OpenstackQuotaHandler** - gathers quota value from instance runtime_properties and do necessary resources names translation for Openstack
* **ResultHandler** - used for *result* instances - dumps current ***ResourceManagementContext*** as runtime_property

## How to extend

Sometimes you may need to write some piece of custom logic for e.g. quota or usage handling. 
Good example is ***OpenstackQuotaHandler*** - it has been introduced because of cohesion in resources naming convention in Openstack.
You can write your own handler.
To do it you need to add new class in ***resource_management_sdk.handlers*** extending ***Handler*** class.
You need to impelment 2 methods:

* ***def can_handle(self, rsm_ctx)*** - returns true if Handler is able to process given type of *instance*
* ***def handle(self, rsm_ctx)*** - contains logic which should be executed for given *instance*

Then you need to add your handler to on handler chain(s) ***SIMPLE_HANDLER_CHAIN*** or / and ***PARALLEL_EXECUTIONS_HANDLER_CHAIN*** in ***resource_management_sdk/__init__.py*** 


## Examples

* **Openstack example** - in *examples/openstack-resources-management* directory. Please read dedicated README file.