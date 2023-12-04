from hashlib import sha256
from ecdsa import SECP256k1, VerifyingKey, SigningKey, util
from ecdsa.util import number_to_string


def generate_keypair_schnorr():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.verifying_key
    return sk, vk


def sign_message_schnorr(private_key, encoded_message):
    curve = SECP256k1
    k = SigningKey.generate(curve=curve).privkey.secret_multiplier
    R = k * curve.generator

    e_hash = sha256(number_to_string(R.x(), curve.order) + encoded_message).digest()
    e = util.string_to_number(e_hash) % curve.order

    s = (k - e * private_key.privkey.secret_multiplier) % curve.order

    r_bytes = number_to_string(R.x(), curve.order)
    s_bytes = number_to_string(s, curve.order)

    return r_bytes+s_bytes


def verify_signature_schnorr(public_key, encoded_message, signature):
    curve = SECP256k1

    r_bytes = signature[:32]
    s_bytes = signature[32:]

    r = util.string_to_number(r_bytes)
    s = util.string_to_number(s_bytes)

    e_hash = sha256(r_bytes + encoded_message).digest()
    e = util.string_to_number(e_hash) % curve.order

    R_check = s * curve.generator + e * public_key.pubkey.point

    return R_check.x() == r


def key_2pc_schnorr(sk1: SigningKey, vk1: VerifyingKey, sk2: SigningKey, vk2: VerifyingKey) -> \
        (SigningKey, VerifyingKey):
    # Aggregate the keys
    aggregated_sk_value = (sk1.privkey.secret_multiplier + sk2.privkey.secret_multiplier) % SECP256k1.order
    aggregated_vk_point = vk1.pubkey.point + vk2.pubkey.point

    # Create a new SigningKey object from the aggregated_sk_value
    aggregated_sk = SigningKey.from_secret_exponent(aggregated_sk_value, curve=SECP256k1)

    # Convert the aggregated public point to a VerifyingKey object
    aggregated_vk = VerifyingKey.from_public_point(aggregated_vk_point, curve=SECP256k1)
    return aggregated_sk, aggregated_vk


def key_3pc_schnorr(sk1: SigningKey, vk1: VerifyingKey, sk2: SigningKey, vk2: VerifyingKey,
                    sk3: SigningKey, vk3: VerifyingKey) -> (SigningKey, VerifyingKey):
    # Aggregate the keys
    aggregated_sk_value = (sk1.privkey.secret_multiplier + sk2.privkey.secret_multiplier +
                           sk3.privkey.secret_multiplier) % SECP256k1.order
    aggregated_vk_point = vk1.pubkey.point + vk2.pubkey.point + vk3.pubkey.point

    # Create a new SigningKey object from the aggregated_sk_value
    aggregated_sk = SigningKey.from_secret_exponent(aggregated_sk_value, curve=SECP256k1)

    # Convert the aggregated public point to a VerifyingKey object
    aggregated_vk = VerifyingKey.from_public_point(aggregated_vk_point, curve=SECP256k1)
    return aggregated_sk, aggregated_vk


def multi_sign_schnorr(aggregated_sk, encoded_message):
    signature = aggregated_sk.sign(encoded_message)
    return signature


def open_2pc_account_schnorr():
    sk1, vk1 = generate_keypair_schnorr()
    sk2, vk2 = generate_keypair_schnorr()
    sk, vk = key_2pc_schnorr(sk1, vk1, sk2, vk2)
    return sk, vk


def open_3pc_account_schnorr():
    sk1, vk1 = generate_keypair_schnorr()
    sk2, vk2 = generate_keypair_schnorr()
    sk3, vk3 = generate_keypair_schnorr()
    sk, vk = key_3pc_schnorr(sk1, vk1, sk2, vk2, sk3, vk3)
    return sk, vk

