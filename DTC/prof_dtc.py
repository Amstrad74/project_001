import os
import re
from collections import defaultdict

# Обновленный список запрещенных байтов (добавлен 0xC2)
FORBIDDEN_BYTES = {
    0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
    0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x3A, 0x3B, 0x3C, 0x3D,
    0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D,
    0x7E, 0x0D, 0x0A
}


def get_words_and_separators(text):
    pattern = re.compile(
        r'([^\x00-\x20\x7F-\xA0]+)|([\x00-\x20\x7F-\xA0])',
        re.UNICODE
    )
    tokens = []
    for match in pattern.finditer(text):
        word, sep = match.groups()
        if word:
            tokens.append(word)
        elif sep:
            tokens.append(sep)
    return tokens


def create_dictionary(tokens):
    word_counts = defaultdict(int)
    for token in tokens:
        if len(token) > 1 or (len(token) == 1 and ord(token[0]) not in FORBIDDEN_BYTES):
            word_counts[token] += 1

    sorted_words = sorted(
        word_counts.items(),
        key=lambda x: (-x[1], -len(x[0]), x[0])
    )

    dictionary = {}
    used_keys = set()
    current_key = 0x01

    for word, _ in sorted_words:
        while current_key in FORBIDDEN_BYTES or current_key in used_keys:
            current_key = (current_key + 1) % 0x100
            if current_key == 0x00:
                current_key = 0x01

        if current_key in FORBIDDEN_BYTES:
            raise ValueError("Недостаточно свободных ключей")

        dictionary[word] = bytes([current_key])
        used_keys.add(current_key)
        current_key += 1
        if current_key > 0xFF:
            current_key = 0x01

    return dictionary


def encrypt_file(input_path, output_dtc_path, output_dict_path):
    # Чтение с поддержкой BOM
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        text = f.read()

    tokens = get_words_and_separators(text)
    dictionary = create_dictionary(tokens)

    encrypted_data = bytearray()
    for token in tokens:
        if token in dictionary:
            encrypted_data.extend(dictionary[token])
        else:
            # Сохраняем оригинальные байты
            encrypted_data.extend(token.encode('utf-8'))

    os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
    with open(output_dtc_path, 'wb') as f:
        f.write(encrypted_data)

    with open(output_dict_path, 'w', encoding='utf-8') as f:
        for word, key in dictionary.items():
            f.write(f"{key.hex()} {word}\n")


def decrypt_file(input_dtc_path, output_path, dict_path):
    dictionary = {}
    with open(dict_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(' ', 1)
            if len(parts) == 2:
                key_hex, word = parts
                try:
                    dictionary[bytes.fromhex(key_hex)] = word
                except ValueError:
                    continue

    with open(input_dtc_path, 'rb') as f:
        encrypted_data = f.read()

    decrypted = []
    i = 0
    while i < len(encrypted_data):
        byte = encrypted_data[i:i + 1]
        if byte in dictionary:
            decrypted.append(dictionary[byte])
            i += 1
        else:
            # Декодируем как UTF-8
            try:
                char = encrypted_data[i:i + 1].decode('utf-8')
                decrypted.append(char)
                i += 1
            except UnicodeDecodeError:
                # Обработка многобайтовых символов
                try:
                    char = encrypted_data[i:i + 2].decode('utf-8')
                    decrypted.append(char)
                    i += 2
                except:
                    decrypted.append('\uFFFD')  # Символ замены
                    i += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write(''.join(decrypted))


if __name__ == "__main__":
    input_filename = 'Призрак.txt'
    base_name = os.path.splitext(input_filename)[0]

    encrypt_file(
        os.path.join('txt', input_filename),
        os.path.join('dtc', base_name + '.dtc'),
        os.path.join('dtc', base_name + '.dtl')
    )

    decrypt_file(
        os.path.join('dtc', base_name + '.dtc'),
        os.path.join('decript', input_filename),
        os.path.join('dtc', base_name + '.dtl')
    )