# AWS Custom Identity Broker

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
