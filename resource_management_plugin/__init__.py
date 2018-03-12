from cloudify.exceptions import NonRecoverableError
from cloudify_rest_client.exceptions import CloudifyClientError


def get_profile(rest_client, profile_name, profile_str):
    if profile_name:
        return _get_profile_from_secret_store(rest_client, profile_name)

    if not profile_str:
        raise NonRecoverableError(
            'One on input parameters: "profile_name" or "profile_str" '
            'need to be defined. Both are empty.'
        )

    return profile_name


def _get_profile_from_secret_store(rest_client, profile_name):
    try:
        return rest_client.secrets.get(key=profile_name)['value']
    except CloudifyClientError as e:
        raise NonRecoverableError(
            'Cannot find {0} profile name as a secret in secrets store. '
            'Details: {1}'
            .format(profile_name, str(e))
        )
