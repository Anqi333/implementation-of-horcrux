from ecdsa import SigningKey, BadSignatureError, VerifyingKey, SECP256k1


def generate_keypair_ecdsa():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key
    return sk, vk


def sign_message_ecdsa(private_key, encoded_message):
    signature = private_key.sign(encoded_message)
    return signature


def verify_signature_ecdsa(verify_key, encoded_message, signature):
    try:
        return verify_key.verify(signature, encoded_message)
    except BadSignatureError:
        return False


def key_2pc_ecdsa(sk1: SigningKey, vk1: VerifyingKey, sk2: SigningKey) -> (SigningKey, VerifyingKey):
    # Aggregate the keys
    aggregated_sk_value = sk1.privkey.secret_multiplier * sk2.privkey.secret_multiplier % SECP256k1.order
    aggregated_vk_point = vk1.pubkey.point.__mul__(sk2.privkey.secret_multiplier)

    # Create a new SigningKey object from the aggregated_sk_value
    aggregated_sk = SigningKey.from_secret_exponent(aggregated_sk_value, curve=SECP256k1)

    # Convert the aggregated public point to a VerifyingKey object
    aggregated_vk = VerifyingKey.from_public_point(aggregated_vk_point, curve=SECP256k1)
    return aggregated_sk, aggregated_vk


def key_3pc_ecdsa(sk1: SigningKey, vk1: VerifyingKey, sk2: SigningKey, sk3: SigningKey) -> (SigningKey, VerifyingKey):
    # Aggregate the keys
    aggregated_sk_value = sk1.privkey.secret_multiplier * sk2.privkey.secret_multiplier * \
                          sk3.privkey.secret_multiplier % SECP256k1.order
    aggregated_vk_point = vk1.pubkey.point.__mul__(sk2.privkey.secret_multiplier * sk3.privkey.secret_multiplier)

    # Create a new SigningKey object from the aggregated_sk_value
    aggregated_sk = SigningKey.from_secret_exponent(aggregated_sk_value, curve=SECP256k1)

    # Convert the aggregated public point to a VerifyingKey object
    aggregated_vk = VerifyingKey.from_public_point(aggregated_vk_point, curve=SECP256k1)
    return aggregated_sk, aggregated_vk


def multi_sign_ecdsa(aggregated_sk, encoded_message):
    signature = aggregated_sk.sign(encoded_message)
    return signature


def open_2pc_account_ecdsa():
    sk1, vk1 = generate_keypair_ecdsa()
    sk2, vk2 = generate_keypair_ecdsa()
    sk, vk = key_2pc_ecdsa(sk1, vk1, sk2)
    return sk, vk


def open_3pc_account_ecdsa():
    sk1, vk1 = generate_keypair_ecdsa()
    sk2, vk2 = generate_keypair_ecdsa()
    sk3, vk3 = generate_keypair_ecdsa()
    sk, vk = key_3pc_ecdsa(sk1, vk1, sk2, sk3)
    return sk, vk
