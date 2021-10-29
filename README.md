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

2. Run the command

```sh
aws-federation-login
```

## インストール

### 開発環境用インストール

```sh
pip install -e .
```

### アンインストール

```sh
pip uninstall -e aws-federation-login
```

## 実行方法

```sh
awsconsole
```

## その他

### 3.10.0 環境だと動作しない

PyInquirer が`prompt_prompt_toolkit`の 1.0.14 に依存していて、1.0.14 では python3.10 ではエラーになるモジュールインポートをしている

```sh
  File "/Users/r-tamura/playground/aws-federation-login-cli/.venv/lib/python3.10/site-packages/prompt_toolkit/styles/from_dict.py", line 9, in <module>
    from collections import Mapping
ImportError: cannot import name 'Mapping' from 'collections' (/Users/r-tamura/.anyenv/envs/pyenv/versions/3.10.0/lib/python3.10/collections/__init__.py)
```

PyInquirer も開発が止まっているっぽいので、新しいバージョンをインストールできない。
TODO: 他のライブラリへ移行すべき
