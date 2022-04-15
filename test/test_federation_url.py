import pytest
from aws_federation_login.federation_url import Credentials, get_signin_token

# request_mockはpytestに付属している
# https://requests-mock.readthedocs.io/en/latest/pytest.html


def test_有効なセッション時間を指定したとき_サインイントークンを取得する(requests_mock):
    # Arrange
    test_sign_token = "test_token"
    requests_mock.get(
        "https://signin.aws.amazon.com/federation", text=f'{{"SigninToken": "{test_sign_token}"}}'
    )
    test_creds = Credentials(
        access_key_id="accesskey", secret_access_key="secret", session_token="token"
    )
    # Act
    actual = get_signin_token(test_creds, 3000)
    # Assert
    assert actual == test_sign_token


def test_有効でないなセッション時間を指定したとき_サインイントークンを取得する(requests_mock):
    # Arrange
    test_sign_token = "test_token"
    requests_mock.get(
        "https://signin.aws.amazon.com/federation", text=f'{{"SigninToken": "{test_sign_token}"}}'
    )
    test_creds = Credentials(
        access_key_id="accesskey", secret_access_key="secret", session_token="token"
    )
    #  Act & Assert
    invalid_duration = 999999
    with pytest.raises(ValueError):
        get_signin_token(test_creds, invalid_duration)
