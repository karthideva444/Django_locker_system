"""
Get ENV value file
"""
import os
from pathlib import Path

from dotenv import load_dotenv

from django.core.exceptions import ImproperlyConfigured

ENV_PATH = ".env"
# print("ENVPATH ::: {} ".format(ENV_PATH))
load_dotenv(dotenv_path=ENV_PATH)


def get_env(env_variable):
    """
    Get ENV value
    """
    try:
        return os.environ[env_variable]
    except KeyError:
        error_msg = "Set the {} environment variable".format(env_variable)
        raise ImproperlyConfigured(error_msg) from None
