# DTC_v1.4.py
# Версия 1.4
import os
import re
import logging
import chardet
from collections import defaultdict
from itertools import product
import heapq


class TextProcessor:
    """Базовый класс для обработки текста"""
    FORBIDDEN_BYTES = {
        0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25,
        0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D,
        0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D, 0x7E, 0x0D, 0x0A, 0x0B,
        0x0C, 0xD0, 0xB1, 0xA7, 0xBD, 0xAB, 0xBB
    }

    MULTIBYTE_SEPARATORS = {
        b'\xC2\xA0',  # Неразрывный пробел
        b'\x0D\x0A',  # CRLF
        b'\xAB',
        b'\xBB',
        b'\xBD',
        b'\xE2\x80\x9C',  # «
        b'\xE2\x80\x9D',  # »
    }

    def __init__(self, input_filename):
        self.input_filename = input_filename
        self.base_name = os.path.splitext(input_filename)[0]
        self.encoding_info = None

    def load_and_detect_encoding(self):
        with open(os.path.join('txt', self.input_filename), 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            self.encoding_info = result
            return raw_data.decode(result['encoding']).encode('utf-8')

    def tokenize(self, data):
        """Токенизация с учетом многобайтовых разделителей"""
        separators = b'|'.join(re.escape(sep) for sep in self.MULTIBYTE_SEPARATORS)
        pattern = re.compile(
            b'((' + separators + b')|[\x00-\x20\xA0\xC2\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E])'
            b'|([^\x00-\x20\xA0\xC2\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E]+)'
        )
        return (match.group(0) for match in pattern.finditer(data))


class AdvancedEncoder(TextProcessor):
    def __init__(self, *args, max_key_length=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_key_length = max_key_length
        self.word_dictionary = {}
        self.reverse_dictionary = {}

    def is_separator(self, token):
        if len(token) == 1:
            return token[0] in self.FORBIDDEN_BYTES
        return token in self.MULTIBYTE_SEPARATORS

    def generate_keys(self):
        allowed_bytes = [b for b in range(0x01, 0x100) if b not in self.FORBIDDEN_BYTES]
        for length in range(1, self.max_key_length + 1):
            for combo in product(allowed_bytes, repeat=length):
                yield bytes(combo)

    def build_dictionary(self, tokens):
        frequency = defaultdict(int)
        for token in tokens:
            if not self.is_separator(token):
                frequency[token] += 1

        # Улучшенная сортировка с приоритетами
        sorted_words = sorted(
            frequency.items(),
            key=lambda x: (-x[1], -len(x[0]), x[0]),
            reverse=False
        )

        key_gen = self.generate_keys()
        used_keys = set()

        for word, _ in sorted_words:
            while True:
                key = next(key_gen)
                if key not in used_keys:
                    self.word_dictionary[word] = key
                    used_keys.add(key)
                    break

    def encrypt_data(self, tokens):
        encrypted = bytearray()
        for token in tokens:
            if self.is_separator(token):
                encrypted.extend(token)
            else:
                encrypted.extend(self.word_dictionary[token])
        encrypted += self.encoding_info['encoding'].encode('utf-8').ljust(20, b'\x00')
        return encrypted

    def encrypt_file(self, output_dtc, output_dict):
        try:
            data = self.load_and_detect_encoding()
            tokens = list(self.tokenize(data))
            self.build_dictionary(tokens)

            with open(output_dict, 'wb') as f:
                for word, key in self.word_dictionary.items():
                    f.write(key + b' ' + word + b'\n')

            encrypted = self.encrypt_data(tokens)
            with open(output_dtc, 'wb') as f:
                f.write(encrypted)

            logging.info(f"Файл зашифрован: {output_dtc}")
            return True

        except Exception as e:
            logging.error(f"Ошибка: {str(e)}")
            return False


class AdvancedDecoder(TextProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reverse_dict = {}
        self.max_key_len = 0

    def load_dictionary(self, dict_path):
        with open(dict_path, 'rb') as f:
            for line in f:
                key, word = line.strip().split(b' ', 1)
                self.reverse_dict[key] = word
                self.max_key_len = max(self.max_key_len, len(key))

    def decrypt_data(self, encrypted_data):
        decrypted = bytearray()
        i = 0
        while i < len(encrypted_data):
            found = False
            for l in range(min(self.max_key_len, len(encrypted_data) - i), 0, -1):
                chunk = encrypted_data[i:i + l]
                if chunk in self.reverse_dict:
                    decrypted.extend(self.reverse_dict[chunk])
                    i += l
                    found = True
                    break
            if not found:
                decrypted.append(encrypted_data[i])
                i += 1
        return decrypted

    def decrypt_file(self, input_dtc, output_path, dict_path):
        try:
            with open(input_dtc, 'rb') as f:
                encrypted_data = f.read()

            encoding = encrypted_data[-20:].split(b'\x00')[0].decode('utf-8')
            encrypted_data = encrypted_data[:-20]

            self.load_dictionary(dict_path)
            decrypted = self.decrypt_data(encrypted_data)

            final_data = decrypted.decode('utf-8').encode(encoding)

            with open(output_path, 'wb') as f:
                f.write(final_data)

            logging.info(f"Файл дешифрован: {output_path}")
            return True

        except Exception as e:
            logging.error(f"Ошибка: {str(e)}")
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    input_file = "test.txt"
    base_name = os.path.splitext(input_file)[0]

    encoder = AdvancedEncoder(input_file)
    encoder.encrypt_file(
        os.path.join('dtc', f'{base_name}.dtc'),
        os.path.join('dtc', f'{base_name}.dtl')
    )

    decoder = AdvancedDecoder(input_file)
    decoder.decrypt_file(
        os.path.join('dtc', f'{base_name}.dtc'),
        os.path.join('decrypted', input_file),
        os.path.join('dtc', f'{base_name}.dtl')
    )
