# Example application

Basic example of an MSE application containing:
- A simple helloworld Flask application
- An MSE app config file
- Unit tests

### Create the mse package with the code and the docker image

__User__: the code provider

```console
$ msehome package --code examples/mse_src/ \
                  --dockerfile examples/Dockerfile \
                  --config examples/mse.home.toml
                  --output workspace/code_provider \
                  --encrypt
```

The generating package can now be sent to the sgx operator.