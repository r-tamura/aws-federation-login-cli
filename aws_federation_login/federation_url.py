import dataclasses
import json
import logging
import tempfile
import typing as t
import webbrowser
from os import mkdir, path
from urllib.parse import quote_plus

import boto3
import requests
from jinja2 import Environment, FileSystemLoader
from PyInquirer import prompt

from .config import load_config_file

Duration = t.Annotated[int, "Seconds"]

logger = logging.getLogger(__name__)


def build_query_string(params: dict[str, str]) -> t.Annotated[str, "?key1=value1&key2=value2"]:
    return "?" + "&".join(map(lambda kv: f"{kv[0]}={kv[1]}", params.items()))


def build_role_arn(account: str, role_name: str) -> str:
    return f"arn:aws:iam::{account}:role/{role_name}"


def app_build_path():
    if not path.exists(BUILD_PATH):
        mkdir(BUILD_PATH)
    return BUILD_PATH


def is_valid_duration(duration: int):
    return 0 < duration < 43200


@dataclasses.dataclass
class Credentials:
    AccessKeyId: str
    SecretAccessKey: str
    SessionToken: str


@dataclasses.dataclass
class AssumeRoleResponse:
    Credentials: Credentials


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
        "sessionId": credentials.AccessKeyId,
        "sessionKey": credentials.SecretAccessKey,
        "sessionToken": credentials.SessionToken,
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


def generate_federation_url(
    *,
    role_arn: t.Optional[str] = None,
    account: t.Optional[str] = None,
    role: t.Optional[str] = None,
    session_name: t.Optional[str],
    duration: Duration = 14400,  # 4 hours
    destination: str,
    mfa_device_arn: t.Optional[str] = None,
) -> str:

    if role_arn is None:
        assert account is not None
        assert role is not None
        role_arn = build_role_arn(account, role)

    if session_name is None:
        session_name = "AnonymousUser"

    sts = boto3.client("sts")
    if mfa_device_arn is not None:
        mfacode = input(f"Enter MFA code for '{mfa_device_arn}': ")
        assumed_role_dict = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            SerialNumber=mfa_device_arn,
            TokenCode=mfacode,
        )
    else:
        assumed_role_dict = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
        )

    credentials = Credentials(
        AccessKeyId=assumed_role_dict["Credentials"]["AccessKeyId"],
        SecretAccessKey=assumed_role_dict["Credentials"]["SecretAccessKey"],
        SessionToken=assumed_role_dict["Credentials"]["SessionToken"],
    )
    signin_token = get_signin_token(credentials, duration)
    request_url = get_signin_url(signin_token, destination)
    return request_url


ASSETS_PATH = path.realpath("assets")
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


def open_link_page(
    url: str, destination: str, template_dir: str, temphtml: tempfile._TemporaryFileWrapper
):
    env = Environment(
        loader=FileSystemLoader(path.join(template_dir, "..", "assets/")),
    )
    template = env.get_template("signin.template.html")
    params = {
        "url": url,
        "destination": destination,
    }
    temphtml.write(template.render(params))
    webbrowser.open(f"file://{temphtml.name}")


def main():
    configs = load_config_file()

    config = None
    if len(configs) == 1:
        config = configs.first
    else:
        name = let_user_choose_config(list(configs.keys()))
        config = configs.get(name)
    assert config is not None

    destination = config.destination
    if destination is None:
        destination = "https://console.aws.amazon.com/"

    url = generate_federation_url(
        role_arn=config.role_arn,
        session_name=config.session_name,
        destination=destination,
        mfa_device_arn=config.mfa_device_arn,
    )

    # output_path = path.join(app_build_path(), "signin.html")
    template_dir = path.dirname(__file__)
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as temphtml:
        open_link_page(
            url=url,
            destination=destination,
            template_dir=template_dir,
            temphtml=temphtml,
        )
