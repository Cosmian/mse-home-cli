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

### Test your app, your docker and your msehome configuration

__User__: the code provider

```console
$ msehome test-dev --code examples/mse_src/ \
                   --dockerfile examples/Dockerfile \
                   --config examples/mse.home.toml \
                   --tests examples/tests/
```

### Create the mse package with the code and the docker image

__User__: the code provider

```console
$ msehome package --code examples/mse_src/ \
                  --dockerfile examples/Dockerfile \
                  --config examples/mse.home.toml \
                  --tests examples/tests/ \
                  --output workspace/code_provider \
                  --encrypt
```

The generating package can now be sent to the sgx operator.

### Spawn the mse docker

__User__: the sgx operator

```console
$ msehome spawn --host localhost \
                --port 7777 \
                --days 345 \
                --signer-key /opt/cosmian-internal/cosmian-signer-key.pem \
                --size 4096 \
                --package workspace/code_provider/package_mse_src_1683276327723953661.tar \
                --output workspace/sgx_operator/ \
                app_name
```

Keep the `workspace/sgx_operator/args.toml` to share it with the other participants. 

### Collect the evidences to verify the application

__User__: the sgx operator

```console
$ msehome evidence --pccs https://pccs.example.com \
                   --signer-key /opt/cosmian-internal/cosmian-signer-key.pem \
                   --output workspace/sgx_operator/ \
                   app_name
```

The file `workspace/sgx_operator/evidence.json` and the previous file `workspace/sgx_operator/args.toml` can now be shared with the orther participants.

### Check the trustworthiness of the application

__User__: the code provider


1. Compute the fingerprint

    ```console
    $ msehome fingerprint --package workspace/code_provider/package_mse_src_1683276327723953661.tar \
                          --args workspace/sgx_operator/args.toml
    ```

    Save the output fingerprint for the next command. 

2. Verify the fingerprint and the enclave information

    ```console
    $ msehome verify --evidence output/evidence.json
                     --fingerprint 6b7f6edd6082c7157a537139f99a20b8fc118d59cfb608558d5ad3b2ba35b2e3
    ```

    If the verification succeed, you can now seal the code key to share it with the sgx operator.

### Seal the code key

__User__: the code provider

TODO

### Finalize the configuration and run the application

__User__: the sgx operator

```console
$ msehome run --key code.secret \
              app_name
```

### Test the deployed application

__User__: the sgx operator

```console
$ msehome test --tests workspace/sgx_operator/tests/ \
               --config workspace/sgx_operator/mse.home.toml \
               app_name
```

### Manage the mse docker

__User__: the sgx operator

You can stop and remove the docker as follow:

```console
$ msehome stop [--remove] <app_name>
```

You can restart a stopped and not removed docker as follow:

```console
$ msehome restart <app_name>
```

You can get the mse docker logs as follow:

```console
$ msehome logs <app_name>
```

You can get the mse docker status as follow:

```console
$ msehome status <app_name>
```

You can get the list of running mse dockers:

```console
$ msehome list
```