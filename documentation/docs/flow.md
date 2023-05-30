In the mse home usage scenario, two roles are defined:

- The code provider. This actor writes and owns the code of the microservice. It could also be the recipient of the result of this application.
- The sgx operator. This actor owns the sgx hardware which runs the code and the data to run against the mse application.

MSE home deals with several trust issues. Noone needs to trust in anyone:

- The code provider can send the code in plaintext or encrypted to the sgx operator. Only the SGX enclave is able to decrypt and run it.
- The code provider can send secrets required by the code in plaintext or encrypted to the sgx operator. Only the SGX enclave is able to decrypt and use them.
- The result of the code can be generated in plaintext or encrypted and readable only by the code provider. Only the code provider could decrypt it.
- The code runs on the SGX technology so the memory is fully encrypted and the code integrity is verifiable at any times. Noone can access the data, the result or the code during execution.

The following flow sums up the chained step from to deploy and run the code by being compliant with the previous privacy & security levels

![](./images/deploy.png)