#credits for the idea go to https://github.com/docker/build-push-action/issues/390#issuecomment-866744086

import os


def get_config_from_environment(env_content):
    # get config from env
    env_content += "DB_URL={}\n".format(os.environ.get("DB_URL", ""))
    env_content += "DB_USER={}\n".format(os.environ.get("DB_USER", ""))
    env_content += "DB_PASSWORD={}\n".format(os.environ.get("DB_PASSWORD", ""))
    env_content += "JWT_SECRET_KEY={}\n".format(os.environ.get("JWT_SECRET_KEY", ""))
    return env_content


env_content = ""
env_content = get_config_from_environment(env_content)

with open(".env", "w", encoding="utf8") as env:
    env.write(env_content)