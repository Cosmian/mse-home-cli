# 🏕️ MSE Home CLI 

MSE Home CLI is designed to start an MSE application on your own SGX hardware without using all the MSE cloud infrastructure. 

We explain later how all the subscommands can be chained to deploy your own application. 

Two actors are required:
- The code provider (who can also consume the result of the MSE application)
- The SGX operator (who also owns the data to run against the MSE application)

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
$ msehome test-dev --project example/
```

### Create the MSE package with the code and the docker image

__User__: the code provider

```console
$ msehome package --project example/ \
                  --output workspace/code_provider 
```

The generated package can now be sent to the sgx operator.

### Spawn the MSE docker

__User__: the SGX operator

```console
$ msehome spawn --host myapp.fr \
                --port 7777 \
                --size 4096 \
                --package workspace/code_provider/package_mse_src_1683276327723953661.tar \
                --output workspace/sgx_operator/ \
                app_name
```

Now, evidences have been automatically collected and the microservice is up.

Evidences are essential for the code provider to verify the trustworthiness of the running application.

The file `workspace/sgx_operator/evidence.json` can now be shared with the other participants.

### Check the trustworthiness of the application

__User__: the code provider

The trustworthiness is established based on multiple information:
- the full code package (tarball)
- the arguments used to spawn the microservice
- evidences captured from the running microservice

Verification of the enclave information:

```console
$ msehome verify --package workspace/code_provider/package_mse_src_1683276327723953661.tar \
                 --evidence output/evidence.json \
                 --output /tmp
```

If the verification succeeds, you get the RA-TLS certificate (written as a file named `ratls.pem`) and you can now seal the code key to share it with the SGX operator.

### Seal your secrets

__User__: the code provider

```console
$ msehome seal --secrets example/secrets_to_seal.json --cert /tmp/ratls.pem  --output workspace/code_provider/
```

### Finalize the configuration and run the application

__User__: the SGX operator

```console
$ msehome run --sealed-secrets workspace/code_provider/secrets_to_seal.json.sealed \
              app_name
```

### Test the deployed application

__User__: the SGX operator

```console
$ msehome test --test workspace/sgx_operator/tests/ \
               --config workspace/sgx_operator/mse.toml \
               app_name
```

### Decrypt the result

__User__: the code provider

Assume the SGX operator gets a result as follow: `curl https://localhost:7788/result --cacert /tmp/ratls.pem > result.enc`

Then, the code provider can decrypt the result has follow:

```console
$ msehome decrypt --aes 00112233445566778899aabbccddeeff \
                  --output workspace/code_provider/result.plain \
                  result.enc
$ cat workspace/code_provider/result.plain
```

### Manage the mse docker

__User__: the SGX operator

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