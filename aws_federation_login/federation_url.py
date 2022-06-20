import dataclasses
import json
import logging
import os
import typing as t
from os import mkdir, path
from urllib.parse import quote_plus

import boto3
import requests
from PyInquirer import prompt

from .config import load_config_file

Duration = t.Annotated[int, "Seconds"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def build_query_string(params: dict[str, str]) -> t.Annotated[str, "?key1=value1&key2=value2"]:
    return "?" + "&".join(map(lambda kv: f"{kv[0]}={kv[1]}", params.items()))


def build_role_arn(account: str, role_name: str) -> str:
    return f"arn:aws:iam::{account}:role/{role_name}"


def app_build_path():
    if not path.exists(BUILD_PATH):
        mkdir(BUILD_PATH)
    return BUILD_PATH


def is_valid_duration(duration: int):
    return 0 < duration <= 43200


@dataclasses.dataclass
class Credentials:
    access_key_id: str
    secret_access_key: str
    session_token: str


@dataclasses.dataclass
class AssumeRoleResponse:
    credentials: Credentials


def get_signin_token(credentials: Credentials, duration: Duration) -> str:
    """
    Args:
        credentials: AWS一時クレデンシャル
    Returns:
        サインイントークン
    """
    if not is_valid_duration(duration):
        raise ValueError("duration must be 0 or more and less than 43200 seconds")

    if credentials is None:
        raise TypeError("AssumeRoleで取得したオブジェクトを指定してください")

    url_credentials = {
        "sessionId": credentials.access_key_id,
        "sessionKey": credentials.secret_access_key,
        "sessionToken": credentials.session_token,
    }
    json_string_with_temp_credentials = json.dumps(url_credentials)
    params = {
        "Action": "getSigninToken",
        "SessionDuration": str(duration),
        "Session": json_string_with_temp_credentials,
    }

    r = requests.get("https://signin.aws.amazon.com/federation", params=params)
    if r.status_code != 200:
        r.raise_for_status()

    return json.loads(r.text)["SigninToken"]


def get_signin_url(signin_token: str, destination: str):
    params = {
        "Action": "login",
        "Issuer": "deepracer.nissan.example",
        "Destination": quote_plus(destination),
        "SigninToken": signin_token,
    }
    request_url = f"https://signin.aws.amazon.com/federation{build_query_string(params)}"
    return request_url


def get_temporary_credentials(
    session_name: t.Optional[str],
    role_arn: t.Optional[str] = None,
    account: t.Optional[str] = None,
    role: t.Optional[str] = None,
    mfa_device_arn: t.Optional[str] = None,
    mfa_code: t.Optional[str] = None,
) -> Credentials:
    if role_arn is None:
        assert account is not None
        assert role is not None
        role_arn = build_role_arn(account, role)

    if session_name is None:
        session_name = "AnonymousUser"

    sts = boto3.client("sts")
    if mfa_device_arn is not None:
        logger.debug("mfa_device_arn was passed")
        if mfa_code is None:
            raise ValueError("please set a mfa code")
        assumed_role_dict = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            SerialNumber=mfa_device_arn,
            TokenCode=mfa_code,
        )
    else:
        logger.debug("mfa_device_arn was not passed")
        assumed_role_dict = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
        )
    credentials = Credentials(
        access_key_id=assumed_role_dict["Credentials"]["AccessKeyId"],
        secret_access_key=assumed_role_dict["Credentials"]["SecretAccessKey"],
        session_token=assumed_role_dict["Credentials"]["SessionToken"],
    )
    return credentials


def generate_federation_url(
    *,
    credentials: Credentials,
    destination: str,
    duration: t.Optional[Duration],
) -> str:
    """一時クレデンシャルからAWSコンソール画面へのサインインURLを作成します。"""
    if duration is None:
        duration = 14400  # 4 hours

    signin_token = get_signin_token(credentials, duration)
    request_url = get_signin_url(signin_token, destination)
    return request_url


BUILD_PATH = path.realpath("__appbuild__")


def let_user_choose_config(names: t.List[str]) -> str:
    answers = prompt(
        [
            {
                "type": "list",
                "name": "profile",
                "message": "Choose a profile",
                "choices": names,
            }
        ]
    )
    choosed_profile_name = answers["profile"]
    return choosed_profile_name


def get_credentials_from_env():
    access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    session_token = os.environ.get("AWS_SESSION_TOKEN")
    if access_key_id and secret_access_key and session_token:
        return Credentials(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
        )
    return None


def get_credentials_from_config() -> tuple[
    Credentials, t.Annotated[t.Optional[str], "destination"]
]:
    configs = load_config_file()

    config = None
    if len(configs) == 1:
        config = configs.first
    else:
        name = let_user_choose_config(list(configs.keys()))
        config = configs.get(name)
    assert config is not None

    destination = config.destination

    mfa_code = None
    if config.mfa_device_arn:
        logger.debug("MFA device ARN: %s", config.mfa_device_arn)
        mfa_code = input(f"Enter MFA code for '{config.mfa_device_arn}': ")

    credentials = get_temporary_credentials(
        role_arn=config.role_arn,
        session_name=config.session_name,
        mfa_device_arn=config.mfa_device_arn,
        mfa_code=mfa_code,
    )
    return credentials, destination


@dataclasses.dataclass
class FederationLoginInfo:
    url: str
    destination: str


def main(
    access_key_id: t.Optional[str] = None,
    secret_access_key: t.Optional[str] = None,
    session_token: t.Optional[str] = None,
    destination: t.Optional[str] = None,
    duration: t.Optional[Duration] = None,
) -> FederationLoginInfo:
    credentials = None
    if access_key_id and secret_access_key and session_token:
        credentials = Credentials(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
        )
        logger.debug("credentials was retrieved from arguments")
    elif (credentials := get_credentials_from_env()) is not None:
        logger.debug("credentials was retrieved from env")
        ...
    else:
        credentials, destination = get_credentials_from_config()

    if destination is None:
        destination = "https://console.aws.amazon.com/"

    url = generate_federation_url(
        credentials=credentials, destination=destination, duration=duration
    )

    return FederationLoginInfo(url=url, destination=destination)
