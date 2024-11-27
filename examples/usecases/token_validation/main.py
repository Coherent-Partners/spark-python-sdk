import jwt  # type: ignore


def validate_token(token: str):
    try:
        unverified = jwt.decode(token, options={'verify_signature': False})
        issuer = unverified.get('iss')

        jwks_client = jwt.PyJWKClient(f'{issuer}/protocol/openid-connect/certs')
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(token, key=signing_key, algorithms=['RS256'], audience='product-factory', issuer=issuer)
        return True, decoded
    except Exception as exc:
        return False, str(exc)


def main():
    TOKEN = 'my_access_token'  # Replace with your token here without 'Bearer ' prefix
    is_valid, _ = validate_token(TOKEN)
    print('Token is', 'valid' if is_valid else 'invalid')


if __name__ == '__main__':
    main()
