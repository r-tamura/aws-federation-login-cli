import logging
import pathlib
import typing as t
from dataclasses import dataclass

import toml

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

DEFAULT_CONFIG_FILE_NAME = "config.toml"



@dataclass
class Config:
    role_arn: str
    session_name: t.Optional[str] = None
    """ サインイン後のリダイレクト先AWS管理コンソール上のURL """
    destination: t.Optional[str] = None
    mfa_device_arn: t.Optional[str] = None
    """ セッション満了までの時間(秒) """
    duration: t.Optional[str] = None


@dataclass
class ConfigMap:
    configs: dict[t.Annotated[str, "name"], Config]

    @property
    def first(self) -> Config:
        return list(self.configs.values())[0]

    def __len__(self):
        return len(self.configs)

    def keys(self):
        return self.configs.keys()

    def items(self):
        return self.configs.items()

    def values(self):
        return self.configs.values()

    def get(self, name: str) -> t.Optional[Config]:
        return self.configs.get(name, None)


def discover_config_file(filename: t.Optional[str] = None) -> str:
    if filename is None:
        filename = DEFAULT_CONFIG_FILE_NAME
    candidates = (
        pathlib.Path(".") / filename,
        pathlib.Path.home() / ".config" / "aws_federation_login" / filename,
    )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise OSError(f"{filename} is not found")


def load_config_file(config_path: t.Optional[str] = None) -> ConfigMap:
    if config_path is None:
        config_path = discover_config_file()

    logger.debug(f"loaded config: {config_path}")
    toml_dict = toml.load(config_path)
    profile_map: t.Optional[dict] = toml_dict.get("profile")

    if profile_map is None:
        raise ValueError("no profile found")

    profiles = profile_map.items()
    config_map = {name: Config(**profile) for name, profile in profiles}
    return ConfigMap(configs=config_map)
