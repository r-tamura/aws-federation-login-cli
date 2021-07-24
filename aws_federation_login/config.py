import pathlib
import typing as t
from dataclasses import dataclass

import toml
from PyInquirer import prompt

DEFAULT_CONFIG_FILE_NAME = "awsfederationconfig.toml"
@dataclass
class Config():
    role_arn: str
    session_name: t.Optional[str] = None
    destination: t.Optional[str] = None
    mfa_device_arn: t.Optional[str] = None

def discorver_config(filename: str = None) -> str:
    if filename is None:
        filename = DEFAULT_CONFIG_FILE_NAME
    candidates = (
        pathlib.Path(".") / filename,
        pathlib.Path.home() / ".my_local" / "aws_federation" / filename
    )

    for cand in candidates:
        if cand.exists():
            return str(cand)

    raise OSError(f"{filename} is not found")

def load_config(config_path: t.Optional[str] = None) -> Config:
    if config_path is None:
        config_path = discorver_config()

    toml_dict = toml.load(config_path)
    profile_map: t.Optional[dict] = toml_dict.get("profile")

    if profile_map is None:
        raise ValueError("no profile found")

    profiles = list(profile_map.items())
    if len(profiles) == 1:
        profile = profiles[0][0]
        return Config(**profile)

    answers = prompt([{
        "type": "list",
        "name": "profile",
        "message": "Choose a profile",
        "choices": [name for name, profile in profiles]
    }])

    profile_name = answers["profile"]

    return Config(**profile_map[profile_name])
