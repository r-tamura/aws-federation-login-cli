import json
import typing as t
import webbrowser
from os import mkdir, path
from urllib.parse import quote_plus

import boto3
import requests
from jinja2 import Environment, FileSystemLoader

from .config import load_config

Duration = t.Annotated[int, "Seconds"]

def build_query_string(params: dict[str, str]) -> t.Annotated[str, "?key1=value1&key2=value2"]:
    return "?" + "&".join(map(lambda kv: f"{kv[0]}={kv[1]}", params.items()))

def build_role_arn(account: str, role_name: str) -> str:
    return f"arn:aws:iam::{account}:role/{role_name}"

def app_build_path():
    if not path.exists(BUILD_PATH):
        mkdir(BUILD_PATH)
    return BUILD_PATH


def get_signin_token(assumed_role_object: dict[str, dict[str, str]], duration: Duration) -> str:
    credentials = assumed_role_object.get('Credentials')
    if credentials is None:
        raise TypeError("AssumeRoleで取得したオブジェクトを指定してください")

    url_credentials = {
        'sessionId': credentials.get('AccessKeyId'),
        'sessionKey': credentials.get('SecretAccessKey'),
        'sessionToken': credentials.get('SessionToken'),
    }
    json_string_with_temp_credentials = json.dumps(url_credentials)
    params = {
        'Action': 'getSigninToken',
        'SessionDuration': str(duration),
        'Session': json_string_with_temp_credentials
    }

    r = requests.get(f"https://signin.aws.amazon.com/federation", params=params)
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
    duration: Duration = 14400, # 4 hours
    destination: str,
    mfa_device_arn: t.Optional[str] = None,
) -> str:

    if role_arn is None:
        assert account is not None
        assert role is not None
        role_arn = build_role_arn(account, role)

    if session_name is None:
        session_name = "AnonymousUser"


    sts = boto3.client('sts')
    if mfa_device_arn is not None:
        mfacode = input(f"Enter MFA code for '{mfa_device_arn}': ")
        assumed_role = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            SerialNumber=mfa_device_arn,
            TokenCode=mfacode,
        )
    else:
        assumed_role = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
        )

    signin_token = get_signin_token(assumed_role, duration)
    request_url = get_signin_url(signin_token, destination)
    return request_url

ASSETS_PATH=path.realpath("assets")
BUILD_PATH=path.realpath("__appbuild__")




def main():
    config = load_config()

    destination = config.destination
    if destination is None:
        destination = "https://console.aws.amazon.com/"

    url = generate_federation_url(
        role_arn=config.role_arn,
        session_name=config.session_name,
        destination=destination,
        mfa_device_arn=config.mfa_device_arn
    )

    output_path = path.join(app_build_path(), "signin.html")
    __dirname__ = path.dirname(__file__)
    with open(output_path, "w") as actual:
        env = Environment(
            loader=FileSystemLoader(path.join(__dirname__, "..", "assets/")),
        )
        template = env.get_template("signin.template.html")
        params = {
            "url": url,
            "destination": destination,
        }
        actual.write(template.render(params))

    webbrowser.open(f"file://{output_path}")

