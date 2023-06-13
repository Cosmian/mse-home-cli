!!! info "Welcome to Microservice Encryption Home deployment tutorial"

    To launch your first confidential microservice, follow this tutorial in your favorite terminal.

MSE Home 🏕️ is designed to start an MSE application on your own SGX hardware without using the MSE cloud infrastructure at all. 

We explain later how all the subscommands can be chained to deploy your own application. 

Two actors are required:

- The code provider (who can also consume the result of the MSE application)
- The SGX operator (who also owns the data to run against the MSE application)

Read [the flow page](flow.md) to get more details about the role of each participant and the overall flow.

## Pre-requisites

You have to install and configure an SGX machine before going any further. 

## Install the MSE Home CLI

The CLI tool [`msehome`](https://github.com/Cosmian/mse-home-cli) requires at least [Python](https://www.python.org/downloads/) 3.8 and [OpenSSL](https://www.openssl.org/source/) 1.1.1 series.
It is recommended to use [pyenv](https://github.com/pyenv/pyenv) to manage different Python interpreters.

```{.console}
$ pip3 install mse-home-cli
$ msehome --help
usage: msehome [-h] [--version] {pack,decrypt,evidence,scaffold,list,logs,restart,run,status,seal,spawn,stop,test,test-dev,verify} ...

Microservice Encryption Home CLI - 0.1.0

options:
  -h, --help            show this help message and exit
  --version             version of msehome binary

subcommands:
  {pack,decrypt,evidence,scaffold,list,logs,restart,run,status,seal,spawn,stop,test,test-dev,verify}
    pack                Generate a package containing the Docker image and the code to run on MSE
    decrypt             Decrypt a file encrypted using the sealed key
    evidence            Collect the evidences to verify on offline mode the application and the enclave
    scaffold            create a new boilerplate MSE web application
    list                List the running MSE applications
    logs                Print the MSE docker logs
    restart             Restart an stopped MSE docker
    run                 Finalise the configuration of the application docker and run the application code
    status              Print the MSE docker status
    seal                Seal the secrets to be share with an MSE app
    spawn               Spawn a MSE docker
    stop                Stop and optionally remove a running MSE docker
    test                Test a deployed MSE app
    test-dev            Test a MSE app in a development context
    verify              Verify the trustworthiness of a running MSE web application and get the RA-TLS certificate
```

!!! info "Pre-requisites"

    Before deploying the app, verify that the Docker service is up and your current user is part of Docker group (current user may use the Docker client without privilege)


## Scaffold your app

!!! info User

    This command is designed to be used by the **code provider**


```console
$ msehome scaffold example
$ tree -a example
example/
├── mse.toml
├── Dockerfile
├── mse_src
    ├── app.py
│   └── .mseignore
├── README.md
├── secrets.json
├── secrets_to_seal.json
└── tests
    ├── conftest.py
    └── test_app.py

2 directories, 9 files
```


The `mse_src` is your application directory designed to be started by `msehome` cli. 

The `Dockerfile` should inherit from the `mse-docker-base` and include all dependencies required to run your app. This docker will be run by the SGX operator.

The file `app.py` is a basic Flask application with no extra code. Adapting your own application to MSE does not require any modification to your Python code:

```python
import json
import os
from http import HTTPStatus
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Flask, Response

app = Flask(__name__)

sealed_secret_json = Path(os.getenv("SEALED_SECRETS_PATH"))
secret_json = Path(os.getenv("SECRETS_PATH"))


@app.get("/health")
def health_check():
    """Health check of the application."""
    return Response(response="OK", status=HTTPStatus.OK)


@app.route('/')
def hello():
    """Get a simple example."""
    return "Hello world"


def aes_encrypt(text: bytes, key: bytes) -> bytes:
    """Encrypt a text using AES-CBC."""
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return iv + encryptor.update(text) + encryptor.finalize()


@app.route("/result/secrets")
def result_with_secret():
    """Get a simple result using secrets."""
    return aes_encrypt(
        b"secret message with secrets.json",
        bytes.fromhex(json.loads(secret_json.read_bytes())["key"]),
    )


@app.route("/result/sealed_secrets")
def result_with_sealed_secret():
    """Get a simple result using sealed secrets."""
    return aes_encrypt(
        b"message with sealed_secrets.json",
        bytes.fromhex(json.loads(sealed_secret_json.read_bytes())["key"]),
    )
```

The [configuration file](./configuration.md) is a TOML file used to give information to the SGX operator, allowing to start correctly the application:

```{.toml}
name = "example"
python_application = "app:app"
healthcheck_endpoint = "/health"
tests_cmd = "pytest"
tests_requirements = [
    "cryptography>=40.0.2,<41.0",
    "intel-sgx-ra==2.0a3",
    "pytest==7.2.0",
]
```

This project also contains a test directory enabling you to test this project locally without any MSE consideration and enabling the SGX operator to test the deployed application.

!!! warning "Compatibility with WSGI/ASGI"

    To be compliant with MSE your Python application must be an [ASGI](https://asgi.readthedocs.io) or [WSGI](https://wsgi.readthedocs.io) application. It is not possible to deploy a standalone Python program. 
    In the next example, this documentation will describe how to deploy Flask applications. You can also use other ASGI applications, for instance: FastAPI.

!!! Examples

    Visit [mse-app-examples](https://github.com/Cosmian/mse-app-examples) to find MSE application examples.

## Test your app, your docker and your msehome configuration


!!! info User

    This command is designed to be used by the **code provider**


```console
$ msehome test-dev --project example
```

## Create the MSE package with the code and the docker image

!!! info User

    This command is designed to be used by the **code provider**


```console
$ msehome pack --project example \
               --output workspace/code_provider 
```

This command generates a tarball named `package_<app_name>_<timestamp>.tar`.

The generated package can now be sent to the SGX operator.

## Spawn the mse docker

!!! info User

    This command is designed to be used by the **SGX operator**


```console
$ msehome spawn --host myapp.fr \
                --port 7777 \
                --size 4096 \
                --package workspace/code_provider/package_mse_src_1683276327723953661.tar \
                --output workspace/sgx_operator/ \
                app_name
```

Mandatory arguments are:
- `host`: common name of the certificate generated later on during [verification step](#check-the-trustworthiness-of-the-application)
- `port`: localhost port used by Docker to bind the application
- `size`: memory size (in MB) of the enclave to spawn
- `package`: the MSE application package containing the Docker images and the code
- `output`: directory to write the args file

This command unpacks the tarball (thus a lot of files are created in `output` folder) specified by the `--package` argument, and generates a `args.toml` file, corresponding to arguments used to spawn the container. This file is also needed to [compute the fingerprint](#check-the-trustworthiness-of-the-application) of the microservice.

Keep the `workspace/sgx_operator/args.toml` to share it with other participants. 

## Collect the evidences to verify the application

!!! info User

    This command is designed to be used by the **SGX operator**


```console
$ msehome evidence --pccs https://pccs.example.com \
                   --output workspace/sgx_operator/ \
                   app_name
```

This command collects cryptographic proofs related to the enclave and serialize them as a file named `evidence.json`.

The file `workspace/sgx_operator/evidence.json` and the previous file `workspace/sgx_operator/args.toml` can now be shared with other participants.

## Check the trustworthiness of the application

!!! info User

    This command is designed to be used by the **code provider**


The trustworthiness is established based on multiple information:
- the full code package (tarball)
- the arguments used to spawn the microservice
- evidences captured from the running microservice

Verification of the enclave information:

    ```console
    $ msehome verify --package workspace/code_provider/package_mse_src_1683276327723953661.tar \
                     --args workspace/sgx_operator/args.toml \
                     --evidence output/evidence.json \
                     --output /tmp
    ```

    If the verification succeed, you get the RA-TLS certificate (writte as a file named `ratls.pem`) and you can now seal the code key to share it with the SGX operator.

## Seal your secrets

!!! info User

    This command is designed to be used by the **code provider**

A sealed secrets file is designed to be shared with the application by hidding them from the SGX operator.

```console
$ msehome seal --secrets example/secrets_to_seal.json \
               --cert /tmp/ratls.pem \
               --output workspace/code_provider/
```

In this example, sealed secrets file is generated as `secrets_to_seal.json.sealed` file.

Share the sealed secrets file with the SGX operator.

## Finalize the configuration and run the application

!!! info User

    This command is designed to be used by the **SGX operator**

```console
$ msehome run --sealed-secrets workspace/code_provider/secrets_to_seal.json.sealed \
              --secrets example/secrets.json
              app_name
```

## Test the deployed application

!!! info User

    This command is designed to be used by the **SGX operator**

```console
$ msehome test --test workspace/sgx_operator/tests/ \
               --config workspace/sgx_operator/mse.toml \
               app_name
```

## Decrypt the results

!!! info User

    This command is designed to be used by the **code provider**


### Fetching `/result/secrets` endpoint

First, the SGX operator collects the result (which is encrypted):

```console
$ curl --insecure --cacert /tmp/ratls.pem https://localhost:7788/result/secrets > result.enc
```

This encrypted result is then sent by external means to the code provider.

Finally, the code provider can decrypt the result:

```console
$ msehome decrypt --aes 00112233445566778899aabbccddeeff \
                  --output workspace/code_provider/result.plain \
                  result.enc
$ cat workspace/code_provider/result.plain
secret message with secrets.json
```

Note that the `--aes` parameter is the key contained in `secrets.json`.
Looking back at the Flask code shows that the `/result/secrets` endpoint loads
the env variable `SECRETS_PATH` to get the `key` value, using it to encrypt a text message.

This demonstrates that `secrets.json` file has been well setup for the enclave and is easily accessible through an env variable.

### Fetching `/result/sealed_secrets` endpoint

!!! info Sealed secrets

    From a user perspective, this is exactly the same as fetching `/result/secrets` endpoint.
    Under the hoods, the original JSON file `secrets_to_seal.json` is transfered
    sealed to the enclave (see how to [seal secrets](#seal-your-secrets)).

    When [starting](#finalize-the-configuration-and-run-the-application), 
    the app seamlessly decrypts this file with the enclave's private key, 
    as sealed secrets are encrypted using the enclave's public key.
    Data from `secrets_to_seal.json` is then accessible from the Flask app, through `SEALED_SECRETS_PATH` env variable.

    This is the way to protect secrets from the SGX operator.


First, the SGX operator collects the encrypted result:

```console
$ curl --insecure --cacert /tmp/ratls.pem https://localhost:7788/result/sealed_secrets > result.enc
```

This encrypted result is then sent by external means to the code provider.

Finally, the code provider can decrypt the result:

```console
$ msehome decrypt --aes ffeeddccbbaa99887766554433221100 \
                  --output workspace/code_provider/result.plain \
                  result.enc
$ cat workspace/code_provider/result.plain
```

Note that the `--aes` parameter is the key contained in `secrets_to_seal.json`.
