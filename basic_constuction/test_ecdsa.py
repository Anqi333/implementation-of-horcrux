from bitcoinutils.transactions import TxInput
import binascii
import hashlib
import sig_ecdsa
from sig_ecdsa import multi_sign_ecdsa
from ecdsa import SigningKey, VerifyingKey
from binascii import hexlify
import time
import struct


def hash256(hex_string: bytes) -> str:
    data = binascii.unhexlify(hex_string)
    h1 = hashlib.sha256(data)
    h2 = hashlib.sha256(h1.digest())
    return h2.hexdigest()


def get_txf(input0: TxInput, input1: TxInput, sk_2pc_ai: SigningKey, sk_2pc_ib: SigningKey, c: float,
            pk_3pc_i: VerifyingKey) -> object:
    tx_out = (c, pk_3pc_i.to_string())
    tx = ([input0, input1], [tx_out])

    tx_bi_str = tx_to_string(tx)
    tx_hex = hexlify(tx_bi_str)
    tx_id = hash256(tx_hex)

    sig_0 = multi_sign_ecdsa(sk_2pc_ai, tx_id.encode())
    sig_1 = multi_sign_ecdsa(sk_2pc_ib, tx_id.encode())
    return tx_id, tx, sig_0, sig_1


def get_txc(tx_in: TxInput, sk_3pc: SigningKey, pk_2pc_ai: VerifyingKey, pk_2pc_ib: VerifyingKey,
            c1: float, c2: float):
    tx_out1 = (c1, pk_2pc_ai.to_string())
    tx_out2 = (c2, pk_2pc_ib.to_string())
    tx = ([tx_in], [tx_out1, tx_out2])

    tx_bi_str = tx_to_string(tx)
    tx_hex = hexlify(tx_bi_str)
    tx_id = hash256(tx_hex)

    sig = multi_sign_ecdsa(sk_3pc, tx_id.encode())
    return tx_id, tx, sig


def update_channel(tx_in: TxInput, pk1: VerifyingKey, pk2: VerifyingKey, sk_2pc: SigningKey, c1: float, c2: float):
    tx_out1 = (c1, pk1.to_string())
    tx_out2 = (c2, pk2.to_string())
    tx = ([tx_in], [tx_out1, tx_out2])

    tx_bi_str = tx_to_string(tx)
    tx_hex = hexlify(tx_bi_str)
    tx_id = hash256(tx_hex)

    sig = multi_sign_ecdsa(sk_2pc, tx_id.encode())
    return tx_id, tx, sig


def gen_st_vc(flag_direction: int, c: float, c_sum: float, sk1: SigningKey, sk2: SigningKey):
    time_stamp = int(time.time())
    st_vc = (flag_direction, c, c_sum, time_stamp)
    st_vc_str = f"{flag_direction}|{c}|{c_sum}|{time_stamp}".encode()
    hash_st_vc = hash256(hexlify(st_vc_str))

    sig0_st_vc = sig_ecdsa.sign_message_ecdsa(sk1, hash_st_vc.encode())
    sig1_st_vc = sig_ecdsa.sign_message_ecdsa(sk2, hash_st_vc.encode())
    return st_vc_str, sig0_st_vc, sig1_st_vc


def tx_to_string(tx):
    inputs, outputs = tx
    input_strs = [f"{txid}_{amount}" for txid, amount in inputs]
    output_strs = [f"{amount}_{pk}" for amount, pk in outputs]
    s = "|".join(input_strs) + "|" + "|".join(output_strs)
    return s.encode()


def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])


def get_tx_size(tx):
    inputs, outputs = tx
    total_size = 0

    # input
    for tx_in in inputs:
        index, c = tx_in
        c_hex = float_to_hex(c)
        total_size += len(index) // 2
        total_size += len(c_hex) // 2

    # output
    for tx_out in outputs:
        c, pk_string = tx_out
        c_hex = float_to_hex(c)
        pk_hex = pk_string.hex()
        total_size += len(c_hex) // 2
        total_size += len(pk_hex) // 2

    return total_size

print('Experiment based on ECDSA')
print('------------------------------------')
# private account
sk_a, vk_a = sig_ecdsa.generate_keypair_ecdsa()
str_a = f"{vk_a.to_string()}".encode()
sk_i, vk_i = sig_ecdsa.generate_keypair_ecdsa()
sk_b, vk_b = sig_ecdsa.generate_keypair_ecdsa()


# 2pc account for A,I and I,B
sk_ai, vk_ai = sig_ecdsa.open_2pc_account_ecdsa()
sk_ib, vk_ib = sig_ecdsa.open_2pc_account_ecdsa()

# setup
tx_in0 = ('e6acdb32126079b06c1afffa255760b40bd7d90bdd7df59d2889fc1a6cdb5fc5', 0.5)
tx_in1 = ('576e704a46ae7215310b5b9426383a1aeb0a47fd3f7b279d7a949495bf303d0b', 0.5)
tx_in2 = ('4bf55bf0a0dcb6a781cb413e8159dfd410d24dc7d226ced58aeebaa60957e863', 1.5)
tx_in3 = ('7994a7447f1c9a7f979e139d8825a32a4819bb0df3a253ac82ea9bcde6ed2348', 0.5)

start_time1 = time.time()
sk_3pc_i, vk_3pc_i = sig_ecdsa.open_3pc_account_ecdsa()
txf_id, txf, sig1, sig2 = get_txf(tx_in0, tx_in1, sk_ai, sk_ib, 1, sk_3pc_i)

tx_ai_id, tx_ai, sig_tx_ai = update_channel(tx_in2, vk_a, vk_i, sk_ai, 1, 0.5)
tx_ib_id, tx_ib, sig_tx_ib = update_channel(tx_in3, vk_i, vk_b, sk_ib, 0.5, 1)
end_time1 = time.time()
elapsed_time1 = end_time1 - start_time1
print(f"The setup phase executed in {elapsed_time1 * 1000} ms.")
# ------------------------------------------------------------------
size_txf = get_tx_size(txf)
sum_len_txf = len(txf_id) + size_txf + len(sig1) + len(sig2)
print("size of whole txf:", sum_len_txf)

size_tx_ai = get_tx_size(tx_ai)
sum_len_tx_ai = len(tx_ai_id) + size_tx_ai + len(sig_tx_ai)
print("size of whole tx_ai in setup phase:", sum_len_tx_ai)

size_tx_ib = get_tx_size(tx_ib)
sum_len_tx_ib = len(tx_ib_id) + size_tx_ib + len(sig_tx_ib)
print("size of whole tx_ib in setup phase:", sum_len_tx_ib)
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# update
start_time2 = time.time()
st_vc_str, sig0_st_vc, sig1_st_vc = gen_st_vc(1, 0.1, 0.5, sk_a, sk_b)
end_time2 = time.time()
elapsed_time2 = end_time2 - start_time2
print(f"The update phase executed in {elapsed_time2 * 1000} ms.")
print("size of st_vc:", len(hexlify(st_vc_str))+len(sig0_st_vc)+len(sig1_st_vc))
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# close
tx_in4 = ('d710aa2b6cafd76ae660b8fc20dcb8652da20974a48684822951091b81f9aae0', 1)
tx_in5 = ('9a9324b7bd346e07a25492eb9e06aff263e37b0d71d18ccde62ff06d93c5b608', 1.9)
tx_in6 = ('8d6cc873b13562e6f0688f26415db8a20eb9b5d4584104a77c2e148e413c878b', 1.1)

start_time3 = time.time()
txc_id, txc, sig_tx_c = get_txc(tx_in4, sk_3pc_i, vk_ai, vk_ib, 0.4, 0.6)

tx_ai_id_c, tx_ai_c, sig_tx_ai_c = update_channel(tx_in5, vk_a, vk_i, sk_ai, 0.49999, 1.40001)
tx_ib_id_c, tx_ib_c, sig_tx_ib_c = update_channel(tx_in6, vk_i, vk_b, sk_ib, 0.6, 1.5)
end_time3 = time.time()
elapsed_time3 = end_time3 - start_time3
print(f"The close phase executed in {elapsed_time3 * 1000} ms.")
# ------------------------------------------------------------------
size_txc = get_tx_size(txc)
sum_len_txc = len(txc_id) + size_txc + len(sig_tx_c)
print("size of whole txc:", sum_len_txc)

size_tx_ai_c = get_tx_size(tx_ai_c)
sum_len_tx_ai_c = len(tx_ai_id_c) + size_tx_ai_c + len(sig_tx_ai_c)
print("size of whole tx_ai in close phase:", sum_len_tx_ai_c)

size_tx_ib_c = get_tx_size(tx_ib_c)
sum_len_tx_ib_c = len(tx_ib_id_c) + size_tx_ib_c + len(sig_tx_ib_c)
print("size of whole tx_ib in close phase:", sum_len_tx_ib_c)

