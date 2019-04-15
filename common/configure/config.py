import configparser
import os
import inspect
import logging


global __config
__config = configparser.ConfigParser()
global __env
__env = 'unknown'


def __is_empty(any_structure: object) -> object:
    if any_structure:
        return False
    else:
        return True


def load_config(environment) -> object:
    """

    :param environment:
    :return:
    """
    __logger = logging.getLogger(__name__)
    __logger.info("inside load configure")

    try:
        cwd = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        path = cwd + "/" + "configure.ini"

        print("Log configuration file:" + path)
        global __config
        __config.read(path, encoding='utf-8')

        global __env
        __env = environment
    except:
        import traceback
        __logger.error("UNABLE TO READ CONFIGURATION!!!!!!!!!!!!")
        __logger.error(traceback.format_exc())


def get_config(key):
    """

    :param key:
    :return:
    """
    __logger = logging.getLogger(__name__)

    __logger.info("inside get_config get " + key + " for env " + __env)

    config_value = "unknown"
    env = __env

    if not __is_empty(__config):
        if __config.has_section(env):
            if key in __config[env]:
                config_value = __config[env][key]

    __logger.info("config_value: ")
    __logger.info(config_value)
    return config_value
