# Example application

A basic example of an MSE application containing:
- A simple helloworld Flask application
- An MSE app config file
- Unit tests

You should edit the following files:
- `mse_src/` with your own webservice code
- `Dockerfile` to run your webservice code into a Docker
- `mse.toml` to specify some details for the person who will run your code through the `msehome` cli
- `tests` with the tests code which can be run against your webservice
- `secrets_to_seal.json` and `secrets.json` if necessary to specify your app secrets

### Test your app, your Docker and your msehome configuration

```console
$ msehome test-dev --code mse_src/ \
                   --dockerfile Dockerfile \
                   --config mse.toml \
                   --test tests/
```

### Create the MSE package with the code and the Docker image

```console
$ msehome package --code mse_src/ \
                  --dockerfile Dockerfile \
                  --config mse.toml \
                  --test tests/ \
                  --output code_provider
```
The generated package can now be sent to the SGX operator.
