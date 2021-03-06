import argparse


def str2bin(s, l):
    if l == 64:
        assert len(s) == 8, 'length of the string is not 64 bits'
    elif l == 32:
        assert len(s) == 4, 'length of the string is not 64 bits'

    return ''.join('{:08b}'.format(ord(i)) for i in s)


def bin2hex(b):
    return ''.join('{:x}'.format(int(b[i:i + 4], 2)) for i in range(0, len(b), 4))


def hex2bin(h):
    # assert len(h) == 8, 'length of given hex is not 32 bits'
    return ''.join('{:04b}'.format(int(i, 16)) for i in h)


def bin2int(b):
    # assert len(b) == 64, 'length of bin is not 64 bits'
    return int(b, 2)


def bin2str(b):
    # assert len(b) == 64, 'length of bin is not 64 bits to convert to string'
    return ''.join(chr(int(b[i:i + 8], 2)) for i in range(0, len(b), 8))


def hex2int(h):
    return int(h, 16)


def _xor(a, b):
    assert type(a) == str and type(b) == str, 'there is something wrong with type in XOR'
    assert len(a) == 32 and len(b) == 32, 'lengths of blocks does not match to 64 in XOR'
    return ''.join(str(int(i) ^ int(j)) for i, j in zip(a, b))


def _add(a, b):
    assert type(a) == str and type(b) == str, 'there is something wrong with type in ADD'
    assert len(a) == 32 and len(b) == 32, 'lengths of blocks does not match to 32 in ADD'
    return '{:032b}'.format((bin2int(a) + bin2int(b)) % (2**32))


def _round(block, key, s_boxes):
    assert len(block) == 64, 'Error in round input, len of block is not 64 bits'
    assert len(key) == 32, 'length of key is not 64 bits'
    L, R = block[:len(block) // 2], block[len(block) // 2:]
    xored_L = _xor(L, key)
    R_prime = xored_L

    L_split = [bin2int(xored_L[i:i + 8]) for i in range(0, len(xored_L), 8)]
    assert len(L_split) == 4, 'The splitted L has no 4 elements'
    s_values = [s_boxes[i][L_split[i]] for i in range(4)]

    assert len(s_values[0]) == 32, 's_values are not of 32 bits'

    # add1 -> xor1 -> add2
    result = _add(s_values[3], _xor(s_values[2], _add(s_values[1], s_values[0])))

    assert len(result) == 32, 'output of s-boxes operation is not 32 bits'
    L_prime = _xor(result, R)
    return L_prime + R_prime


def encrypt(block, p_array, s_blocks):
    for key in p_array[:16]:
        block = _round(block, key, s_blocks)

    left_block = block[:32]
    right_block = block[32:]
    right_block, left_block = left_block, right_block
    block = _xor(p_array[17], left_block) + _xor(p_array[16], right_block)
    return block


def generate_sub_keys(key):
    key = key * (72 // len(key)) + key
    key = key[:72]
    keys = [str2bin(key[i:i + 4], 32) for i in range(0, len(key), 4)]

    msg = '00000000'
    msg = str2bin(msg, 64)
    with open('pihex64k.txt', 'r') as f:
        P = [f.read(8) for i in range(18)]
        S = [[f.read(8) for j in range(256)] for k in range(4)]

    P = [hex2bin(i) for i in P]
    for i in range(4):
        for j in range(256):
            S[i][j] = hex2bin(S[i][j])

    P = [_xor(keys[i], P[i]) for i in range(18)]

    for i in range(0, len(P), 2):
        msg = encrypt(msg, P, S)
        P[i] = msg[:32]
        P[i + 1] = msg[32:]

    for i in range(4):
        for j in range(0, 256, 2):
            msg = encrypt(msg, P, S)
            S[i][j] = msg[:32]
            S[i][j + 1] = msg[32:]

    return P, S


def encryption(msg, sub_keys, s_boxes, mode):
    # print(msg)
    if mode == 'e':
        msg = [msg[i:i + 8] for i in range(0, len(msg), 8)]
        # print(msg)
        if len(msg[-1]) < 8:
            msg[-1] += ' ' * (8 - len(msg[-1]))

        msg = [str2bin(i, None) for i in msg]

    elif mode == 'd':
        msg = [hex2bin(msg[i:i + 16]) for i in range(0, len(msg), 16)]

    ciphertext = ''
    for each in msg:
        ciphertext += encrypt(each, sub_keys, s_boxes)

    if mode == 'e':
        cipher = bin2hex(ciphertext)

    if mode == 'd':
        cipher = bin2str(ciphertext)

    return cipher


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', choices=['e', 'd'], required=True, help='Encryption(e) / Decryption(d)')
parser.add_argument('-k', '--key', required=True, help='key for encryption or decryption')
parser.add_argument('-s', '--string', required=True, help='String to be encrypted or decrypted', )
args = parser.parse_args()

message = args.string
password = args.key

sub_keys, s_boxes = generate_sub_keys(password)

# print(message)
if args.mode == 'e':
    enc = encryption(message, sub_keys, s_boxes, 'e')
    print('hex digest:', enc)
elif args.mode == 'd':
    dec = encryption(message, sub_keys[::-1], s_boxes, 'd')
    print(dec)
else:
    print('Invalid choice!')
