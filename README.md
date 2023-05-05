# 🏕️ MSE CLI Home

## Install

```console
$ pip install -r requirements.txt
$ pip install -U .
```

## Usage

```console
$ msehome -h
```

You can find below the use flow step by step.

### Create the mse package

User: the code provider

```console
$ msehome package --code examples/mse_src/ \
                  --output output \
                  --dockerfile examples/Dockerfile \
                  --encrypt
```

The generating package can now be sent to the sgx operator

### Spawn the mse docker

User: the sgx operator

```console
$ msehome spawn --name test_mse_home \
                --host localhost\
                --port 7777\
                --days 345\
                --signer-key /opt/cosmian-internal/cosmian-signer-key.pem\
                --size 4096\
                --package output/package_mse_src_1683276327723953661.tar
```