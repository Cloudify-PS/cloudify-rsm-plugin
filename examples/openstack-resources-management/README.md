# Openstack resource management

Resource availability checking for 2 openstack project. 
To use only one project please comment all parts of global blueprint beginning with "project_2"

1) Create secrets with resource profiles 

```
cfy secrets create resource_profile_test_ok --secret-string '{"global": {}, "project": {"openstack": {"server": 1, "port": 3, "subnet": 3, "network": 3, "security_group": 3}}}'
cfy secrets create resource_profile_test_nok --secret-string '{"global": {}, "project": {"openstack": {"server": 10000, "port": 3, "subnet": 3, "network": 3, "security_group": 3}}}'
```

2) Upload blueprints

```
cfy blueprints upload openstack_project-blueprint.yaml -b rsm_openstack_project
cfy blueprints upload openstack_global-blueprint.yaml -b rsm_openstack_global
```

3) Create deployment

```
cfy deployments create rsm_os_test -b rsm_openstack_global --skip-plugins-validation \
  -i project_blueprint_id='rsm_openstack_project' \
  -i project_1_id='1966cea3c8c048e7a4216dde1583f61d' \
  -i project_1_name='cfy_test_project' \
  -i project_2_id='4e79b0b7165843afa0d861b65ac87665' \
  -i project_2_name='admin'
```

4) Install deployment

```
cfy executions start install -d rsm_os_test
```

5) Run 'check_resources_availability' workflow for resource profile which requires low amount of resources. Execution should ended successfully.

```
cfy executions start -d rsm_os_test check_resources_availability -p profile_name=resource_profile_test_ok -p project_id=cfy_test_project -vv
```

6) Run 'check_resources_availability' workflow for resource profile which requires high amount of resources. Execution should fail and error should be related to number of required servers.

```
cfy executions start -d rsm_os_test check_resources_availability -p profile_name=resource_profile_test_nok -p project_id=cfy_test_project -vv
```

Error should be similar to:
 
```
Profile requirement not met for resource: openstack/server in project: cfy_test_project. Requirement is server=10000.0, but only 9.0 is available
```

7)  Uninstall deployment:

```
cfy uninstall rsm_os_test
```

8) Delete project blueprint

```
cfy blueprints delete rsm_openstack_project
```

9) Delete secrets

```
cfy secrets delete resource_profile_test_ok
cfy secrets delete resource_profile_test_nok
```
