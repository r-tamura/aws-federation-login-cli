import json
import webbrowser
from os import mkdir, path
from typing import Annotated, Optional
from urllib.parse import quote_plus

import boto3
import requests

Duration = Annotated[int, "Seconds"]

def build_query_string(params: dict[str, str]) -> Annotated[str, "?key1=value1&key2=value2"]:
    return "?" + "&".join(map(lambda kv: f"{kv[0]}={kv[1]}", params.items()))


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
        'Session': quote_plus(json_string_with_temp_credentials)
    }

    request_url = f"https://signin.aws.amazon.com/federation{build_query_string(params)}"
    r = requests.get(request_url)
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
    account: str,
    role: str,
    session_name: str,
    duration: Duration = 14400, # 4 hours
    destination: str = "https://console.aws.amazon.com/",
    mfa_device_arn: Optional[str],
) -> str:

    sts = boto3.client('sts')
    if mfa_device_arn is not None:
        mfacode = input(f"Enter MFA code for '{mfa_device_arn}': ")
        assumed_role = sts.assume_role(
            RoleArn=f"arn:aws:iam::{account}:role/{role}",
            RoleSessionName=session_name,
            SerialNumber=mfa_device_arn,
            TokenCode=mfacode,
        )
    else:
        assumed_role = sts.assume_role(
            RoleArn=f"arn:aws:iam::{account}:role/{role}",
            RoleSessionName=session_name,
        )

    signin_token = get_signin_token(assumed_role, duration)
    request_url = get_signin_url(signin_token, destination)
    return request_url

ASSETS_PATH=path.realpath("assets")
BUILD_PATH=path.realpath("__appbuild__")

def app_build_path():
    if not path.exists(BUILD_PATH):
        mkdir(BUILD_PATH)
    return BUILD_PATH


def main():
    url = generate_federation_url(
        account="991720041588",
        role="DeepRacerTrainingRole",
        session_name="TrainingUserA",
        destination="https://console.aws.amazon.com/deepracer/home?region=us-east-1#league",
        mfa_device_arn="arn:aws:iam::878754454461:mfa/tamura-r"
    )
    template_path = path.join(ASSETS_PATH, "signin.template.html")
    output_path = path.join(app_build_path(), "signin.html")
    with open(template_path) as template, open(output_path, "w") as actual:
        actual.write(template.read().replace("{{url}}", url))


    webbrowser.open(f"file://{output_path}")
