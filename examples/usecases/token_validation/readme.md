## Validate JWTs against Keycloak

This example demonstrates how to decode and validate JSON web tokens (JWT) or bearer
tokens issued by [Keycloak].

Keycloak is the identity and access management solution used by Coherent Spark to
secure its services. It issues JWTs that can be used to authenticate and authorize
requests to the services.

There are scenarios such as [Xconnector] where you need to implement a remote service
that requires a bearer token to be passed in the request header. In order to trust
that token, you need to validate its signature against the Keycloak server before
proceeding with the request.

## Setup and Testing

To test this example, grab a JWT (without the prefix `Bearer`) issued by Keycloak
and modify the `TOKEN` variable in [main.py](main.py) with the JWT. Then, run the
following command:

```bash
poetry run python main.py
```

The script will decode the JWT using [pyjwt] and validate its signature against
Spark's Keycloak server. If and when the token is valid, `validate_token()` returns
a tuple that includes the validation status (i.e.,`True`) and the decoded token as
a dictionary.

<!-- References -->
[Keycloak]: https://www.keycloak.org/
[xconnector]: https://docs.coherent.global/xconnector/introduction-to-xconnector
[pyjwt]: https://pyjwt.readthedocs.io/en/stable/usage.html#encoding-decoding-tokens-with-rs256-rsa
