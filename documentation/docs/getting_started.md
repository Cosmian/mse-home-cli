!!! info "Welcome to Microservice Encryption Home deployment tutorial"

    To launch your first confidential microservice, follow this tutorial in your favorite terminal.

MSE Home 🏕️ is designed to start an mse application on your own SGX hardware without using all the mse cloud infrastructure. 

We explain later how all the subscommands can be chained to deploy your own application. 

Two actors are required:

- The code provider (who can also consume the result of the mse application)
- The sgx operator (who also owns the data to run against the mse application)

Read [the flow page](flow.md) to get more details about the role of each participant and the overall flow.

## Pre-requesites

You have to install and configure an SGX machine before going any further. 

## Install

The CLI tool [`msehome`](https://github.com/Cosmian/mse-home-cli) requires at least [Python](https://www.python.org/downloads/) 3.8 and [OpenSSL](https://www.openssl.org/source/) 1.1.1 series.
It is recommended to use [pyenv](https://github.com/pyenv/pyenv) to manage different Python interpreters.

```{.console}
$ pip3 install mse-home-cli
$ msehome --help
usage: msehome [-h] [--version] {package,decrypt,evidence,fingerprint,scaffold,list,logs,restart,run,status,seal,spawn,stop,test,test-dev,verify} ...

Microservice Encryption Home CLI - 0.1.0

options:
  -h, --help            show this help message and exit
  --version             version of msehome binary

subcommands:
  {package,decrypt,evidence,fingerprint,scaffold,list,logs,restart,run,status,seal,spawn,stop,test,test-dev,verify}
    package             Generate a package containing the docker image and the code to run on MSE
    decrypt             Decrypt a file encrypted using the sealed key
    evidence            Collect the evidences to verify on offline mode the application and the enclave
    fingerprint         Compute the code fingerprint
    scaffold            create a new boilerplate MSE web application
    list                List the running MSE applications
    logs                Print the MSE docker logs
    restart             Restart an stopped MSE docker
    run                 Finalise the configuration of the application docker and run the application code
    status              Print the MSE docker status
    seal                Seal the secrets to be share with an MSE app
    spawn               Spawn a MSE docker
    stop                Stop and remove a running MSE docker
    test                Test a deployed mse app
    test-dev            Test a mse app when developing it
    verify              Verify the trustworthiness of a running MSE web application and get the ratls certificate
```

!!! info "Pre-requisites"

    Before deploying the app, verify that docker service is up and your current user can use the docker client without privilege


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

The `Dockerfile` should inherit from the `mse-docker-base` and include all dependencies required to run your app. This docker will be run by the sgx operator.

The file `app.py` is a basic Flask application with no extra code. Adapt your own application to MSE does not require any modification to your Python code:

```python
from http import HTTPStatus
from flask import Flask, Response

app = Flask(__name__)


@app.get("/health")
def health_check():
    """Health check of the application."""
    return Response(status=HTTPStatus.OK)


@app.route('/')
def hello():
    """Get a simple example."""
    return "Hello world"


if __name__ == "__main__":
    app.run(debug=True)

```

The [configuration file](./configuration.md) is a TOML file to give information to the sgx operator enables him to start the application:

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

This project also contains a test directory enabling you to test this project locally without any MSE consideration and enabling the sgx operator to test the deployed application.

!!! warning "Compatibility with WSGI/ASGI"

    To be compliant with MSE your Python application must be an [ASGI](https://asgi.readthedocs.io) or [WSGI](https://wsgi.readthedocs.io) application. It is not possible to deploy a standalone Python program. 
    In the next example, this documentation will describe how to deploy Flask applications. You also can use other ASGI applications, for instance: FastAPI.

!!! Examples

    Visit [mse-app-examples](https://github.com/Cosmian/mse-app-examples) to find MSE application examples.

## Test your app, your docker and your msehome configuration


!!! info User

    This command is designed to be used by the **code provider**

```console
$ msehome test-dev --code example/mse_src/ \
                   --dockerfile example/Dockerfile \
                   --config example/mse.toml \
                   --test example/tests/
```

## Create the mse package with the code and the docker image

!!! info User

    This command is designed to be used by the **code provider**

```console
$ msehome package --code example/mse_src/ \
                  --dockerfile example/Dockerfile \
                  --config example/mse.toml \
                  --test example/tests/ \
                  --output workspace/code_provider 
```

The generating package can now be sent to the sgx operator.

## Spawn the mse docker

!!! info User

    This command is designed to be used by the **sgx operator**



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

## Collect the evidences to verify the application

!!! info User

    This command is designed to be used by the **sgx operator**



```console
$ msehome evidence --pccs https://pccs.example.com \
                   --output workspace/sgx_operator/ \
                   app_name
```

The file `workspace/sgx_operator/evidence.json` and the previous file `workspace/sgx_operator/args.toml` can now be shared with the orther participants.

## Check the trustworthiness of the application

!!! info User

    This command is designed to be used by the **code provider**


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

## Seal your secrets

!!! info User

    This command is designed to be used by the **code provider**

A seal secrets file is designed to be share with the application by hidding them from the sgx operator.

```console
$ msehome seal --secrets example/secrets_to_seal.json --cert /tmp/ratls.pem  --output workspace/code_provider/
```

Share the sealed secrets file with the sgx operator.

## Finalize the configuration and run the application

!!! info User

    This command is designed to be used by the **sgx operator**

```console
$ msehome run --sealed-secrets workspace/code_provider/secrets_to_seal.json.sealed \
              app_name
```

## Test the deployed application

!!! info User

    This command is designed to be used by the **sgx operator**

```console
$ msehome test --test workspace/sgx_operator/tests/ \
               --config workspace/sgx_operator/mse.toml \
               app_name
```

## Decrypt the result

!!! info User

    This command is designed to be used by the **code provider**

Assume the sgx operator gets a result as follow: `curl https://localhost:7788/result --cacert /tmp/ratls.pem > result.enc`

Then, the code provider can decrypt the result has follow:

```console
$ msehome decrypt --aes 00112233445566778899aabbccddeeff \
                  --output workspace/code_provider/result.plain \
                  result.enc
$ cat workspace/code_provider/result.plain
```

