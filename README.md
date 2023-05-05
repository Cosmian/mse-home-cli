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

__User__: the code provider

```console
$ msehome package --code examples/mse_src/ \
                  --output output \
                  --dockerfile examples/Dockerfile \
                  --encrypt
```

The generating package can now be sent to the sgx operator

### Spawn the mse docker

__User__: the sgx operator

```console
$ msehome spawn --host localhost \
                --port 7777 \
                --days 345 \
                --signer-key /opt/cosmian-internal/cosmian-signer-key.pem \
                --size 4096 \
                --package output/package_mse_src_1683276327723953661.tar \
                test_mse_home
```


### Manage the mse docker

__User__: the sgx operator

You can stop and remove the docker as follow:

```console
$ msehome stop <test_mse_home>
```

You can get the mse docker logs as follow:

```console
$ msehome logs <test_mse_home>
```

You can get the mse docker status as follow:

```console
$ msehome status <test_mse_home>
```