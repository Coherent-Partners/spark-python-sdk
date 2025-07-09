from sys import version_info as v

__all__ = ['__version__', '__title__', 'sdk_version', 'about']

__version__ = sdk_version = '0.2.0'

__title__ = 'Coherent Spark Python SDK'

sdk_logger = f'CSPARK v{sdk_version}'

platform_info = f'Python/{v.major}.{v.minor}.{v.micro}'

about = f'Coherent Spark SDK v{sdk_version} ({platform_info})'

sdk_ua_header = f'agent=spark-python-sdk/{sdk_version}; env={platform_info}'
