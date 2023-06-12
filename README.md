# 🏕️ MSE Home CLI 

MSE Home CLI is designed to start an mse application on your own SGX hardware without using all the mse cloud infrastructure. 

We explain later how all the subscommands can be chained to deploy your own application. 

Two actors are required:
- The code provider (who can also consume the result of the mse application)
- The sgx operator (who also owns the data to run against the mse application)

## Install

```console
$ pip install -r requirements.txt
$ pip install -U .
```

## Test

```console
$ export TEST_PCCS_URL="https://pccs.staging.mse.cosmian.com" 
$ export TEST_SIGNER_KEY="/opt/cosmian-internal/cosmian-signer-key.pem"
$ pytest
```

## Usage

```console
$ msehome -h
```

You can find below the use flow step by step.

### Scaffold your app

__User__: the code provider

```console
$ msehome scaffold example
```

### Test your app, your docker and your msehome configuration

__User__: the code provider

```console
$ msehome test-dev --code example/mse_src/ \
                   --dockerfile example/Dockerfile \
                   --config example/mse.toml \
                   --test example/tests/
```

### Create the mse package with the code and the docker image

__User__: the code provider

```console
$ msehome package --code example/mse_src/ \
                  --dockerfile example/Dockerfile \
                  --config example/mse.toml \
                  --test example/tests/ \
                  --output workspace/code_provider 
```

The generating package can now be sent to the sgx operator.

### Spawn the mse docker

__User__: the sgx operator

```console
$ msehome spawn --host myapp.fr \
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
    $ msehome verify --evidence output/evidence.json \
                     --fingerprint 6b7f6edd6082c7157a537139f99a20b8fc118d59cfb608558d5ad3b2ba35b2e3 \
                     --output /tmp
    ```

    If the verification succeed, you get the ratls certificat and you can now seal the code key to share it with the sgx operator.

### Seal your secrets

__User__: the code provider

```console
$ msehome seal --secrets example/secrets_to_seal.json --cert /tmp/ratls.pem  --output workspace/code_provider/
```

### Finalize the configuration and run the application

__User__: the sgx operator

```console
$ msehome run --sealed-secrets workspace/code_provider/secrets_to_seal.json.sealed \
              app_name
```

### Test the deployed application

__User__: the sgx operator

```console
$ msehome test --test workspace/sgx_operator/tests/ \
               --config workspace/sgx_operator/mse.toml \
               app_name
```

### Decrypt the result

__User__: the code provider

Assume the sgx operator gets a result as follow: `curl https://localhost:7788/result --cacert /tmp/ratls.pem > result.enc`

Then, the code provider can decrypt the result has follow:

```console
$ msehome decrypt --aes 00112233445566778899aabbccddeeff \
                  --output workspace/code_provider/result.plain \
                  result.enc
$ cat workspace/code_provider/result.plain
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