import os
from yaml import safe_load
from logging import config, basicConfig


def _convert_filenames_to_abspath(config_dict):
    """ to scan thru the configuration for the file paths
        and get the absoulte path specific to the os.
        and if required create the directories as per the specification.
    """
    for k, v in config_dict.items():
        if isinstance(v, dict):
            _convert_filenames_to_abspath(v)
        elif k == 'filename':
            file_path = os.path.abspath(v)
            file_directory = os.path.dirname(file_path)
            if not os.path.exists(file_directory):
                os.makedirs(file_directory)
            config_dict[k] = file_path


def set_loggers(default_path='logger.yaml', default_level="INFO", env_key='LOG_LC'):
    """
    Creating the required loggers as per the specifications in configuration file

    :param default_path: path for configuration file
    :param default_level: logger default level
    :param env_key: configuration key to look for the configuration file path
    """
    file_path = os.path.abspath(default_path)
    value = os.getenv(env_key, None)

    if value:
        file_path = os.path.abspath(value)
    if os.path.exists(file_path):
        with open(file_path, 'rt') as f:
            config_file = safe_load(f.read())
            print(config_file)
            _convert_filenames_to_abspath(config_file)
            config.dictConfig(config_file)
    else:
        basicConfig(level=default_level)


