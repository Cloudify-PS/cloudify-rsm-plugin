import setuptools

setuptools.setup(
    name='cloudify_resource_management',
    version='0.0.2',
    author='Krzysztof Bijakowski',
    author_email='krzysztof.bijakowski@cloudify.co',
    description='Resources tracking & quota validation',
    packages=[
        'resource_management_plugin',
        'resource_management_sdk'
    ],
    license='LICENSE',
    install_requires=[
        'cloudify-plugins-common>=3.4.2',
        'cloudify-rest-client>=4.0',
        'xmltodict'
    ]
)
