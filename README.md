# AWS Federation Login CLI

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

### インストール

```shell
pip install git+https://github.com/r-tamura/aws-federation-login-cli.git
```

### アンインストール

```shell
pip uninstall aws-federation-login
```

## 開発

```shell
git clone https://github.com/r-tamura/aws-federation-login-cli.git
cd aws-federation-login-cli
pip install -e .
```

## 実行方法

```shell
aws-federation-login
```

## その他

### 3.10.0 環境だと動作しない

PyInquirerが`prompt_prompt_toolkit`の1.0.14に依存していて、1.0.14ではpython3.10でエラーになるモジュールインポートをしている

```sh
  File "/Users/r-tamura/playground/aws-federation-login-cli/.venv/lib/python3.10/site-packages/prompt_toolkit/styles/from_dict.py", line 9, in <module>
    from collections import Mapping
ImportError: cannot import name 'Mapping' from 'collections' (/Users/r-tamura/.anyenv/envs/pyenv/versions/3.10.0/lib/python3.10/collections/__init__.py)
```

PyInquirerも開発が止まっているっぽいので、新しいバージョンをインストールできない。
TODO: 他のライブラリへ移行すべき
