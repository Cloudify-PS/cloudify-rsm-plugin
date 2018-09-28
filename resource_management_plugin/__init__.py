from cloudify.exceptions import NonRecoverableError
from cloudify_rest_client.exceptions import CloudifyClientError


def get_profile(rest_client, profile_name, profile_str):
    """Get profile by name or default value from parameters.

    Code have tried to get profile description by 'profile_name' from
    secrets storage and if profile in secrets is empty returns default
    value from 'profile_str' as default value.

    Args:
        rest_client: cfy rest client
        profile_name: profile name in secrets storage
        profile_str: default value for profile if no such in secrets storage.

    Returns:
        Json string with profile description.

    Raises:
        NonRecoverableError: Can't get profile from secrets store or directly
            from parameters."""
    if profile_name:
        return _get_profile_from_secret_store(rest_client, profile_name)

    if not profile_str:
        raise NonRecoverableError(
            'One on input parameters: "profile_name" or "profile_str" '
            'need to be defined. Both are empty.'
        )

    return profile_str


def _get_profile_from_secret_store(rest_client, profile_name):
    """Get profile from secrets storage by connection to cloudify manager.

    Args:
        rest_client: rest client instance
        profile_name: profile name

    Returns:
        Json string with profile description.

    Raises:
        NonRecoverableError: Can't get profile from secrets store."""
    try:
        return rest_client.secrets.get(key=profile_name)['value']
    except CloudifyClientError as e:
        raise NonRecoverableError(
            'Cannot find {0} profile name as a secret in secrets store. '
            'Details: {1}'
            .format(profile_name, str(e))
        )
