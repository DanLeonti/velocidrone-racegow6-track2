import base64, sys, json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
def key_from_seed(seed):
    k8 = seed.replace(' ', '')[:8]
    return (k8 + k8[::-1]).encode()
def decrypt(b64text, seed='Velocidrone'):
    data = base64.b64decode(''.join(b64text.split()))
    c = Cipher(algorithms.AES(key_from_seed(seed)), modes.ECB()).decryptor()
    pt = c.update(data) + c.finalize()
    pad = pt[-1]
    if 1 <= pad <= 16 and pt.endswith(bytes([pad])*pad): pt = pt[:-pad]
    return pt.decode('utf-8', errors='replace')
def encrypt(text, seed='Velocidrone'):
    raw = text.encode('utf-8'); pad = 16 - len(raw) % 16; raw += bytes([pad])*pad
    c = Cipher(algorithms.AES(key_from_seed(seed)), modes.ECB()).encryptor()
    return base64.b64encode(c.update(raw) + c.finalize()).decode()
if __name__ == '__main__':
    mode, seed, path = sys.argv[1], sys.argv[2], sys.argv[3]
    t = open(path).read()
    sys.stdout.write(decrypt(t, seed) if mode == 'dec' else encrypt(t, seed))
