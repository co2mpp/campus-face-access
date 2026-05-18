"""
AES-256-GCM 加解密工具模块
- 加密：随机生成12字节IV，输出 IV(12) + 认证标签(16) + 密文
- 解密：验证认证标签后返回明文
"""
import os
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def generate_key() -> bytes:
    """生成256位随机密钥并Base64编码返回"""
    return get_random_bytes(32)


def encode_key(key: bytes) -> str:
    return base64.b64encode(key).decode('ascii')


def decode_key(encoded: str) -> bytes:
    return base64.b64decode(encoded)


def encrypt_feature(feature_bytes: bytes, key: bytes) -> tuple:
    """
    加密特征向量
    :param feature_bytes: 512维float32特征 → 2048字节
    :param key: 32字节AES-256密钥
    :return: (iv: bytes(12), ciphertext_with_tag: bytes)
    """
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(feature_bytes)
    # 密文 + 16字节认证标签拼接
    return iv, ciphertext + tag


def decrypt_feature(iv: bytes, ciphertext_with_tag: bytes, key: bytes) -> bytes:
    """
    解密特征向量
    :param iv: 12字节初始化向量
    :param ciphertext_with_tag: 密文(前n-16字节) + 认证标签(后16字节)
    :param key: 32字节AES-256密钥
    :return: 2048字节明文特征
    """
    tag = ciphertext_with_tag[-16:]
    ciphertext = ciphertext_with_tag[:-16]
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext


if __name__ == '__main__':
    # 自测
    key = generate_key()
    print(f"密钥 (Base64): {encode_key(key)}")
    test_data = os.urandom(2048)
    iv, ct = encrypt_feature(test_data, key)
    print(f"IV长度={len(iv)}, 密文+标签长度={len(ct)}")
    pt = decrypt_feature(iv, ct, key)
    assert pt == test_data, "加解密验证失败！"
    print("加解密验证通过！")
