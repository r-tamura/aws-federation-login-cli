# AWS Federation Login CLI

A tool to generate an URL for Sign in AWS Management Console using [AWS federation endpoint](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_enable-console-custom-url.html)


## How to use

1. Create a config file in `$HOME/.config/aws_federation_cli/config.toml`

    ```shell
    [profile.<name>]
    role_arn = "arn:aws:iam::9999999999:role/YourRole"
    destination = "https://console.aws.amazon.com/console/home?region=us-east-1"
    duration = 43200
    session_name = "<session name>"
    ```

1. Run the command

    ```shell
    aws-federation-login
    ```

## Install

```shell
pip install git+https://github.com/r-tamura/aws-federation-login-cli.git
```

## Development

```shell
git clone https://github.com/r-tamura/aws-federation-login-cli.git
cd aws-federation-login-cli
pip install -e .
```

- `requirements-dev.txt`の更新

```shell
pip freeze --exclude-editable > requirements-dev.txt
```

