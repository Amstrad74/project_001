

# Версия 1.3
# Работает с utf-8 txt без ошибок, побайтовое совпадение.
# попытка сделать независимую от кодировки версию.

import os
import re
from collections import defaultdict
from itertools import product
import logging
import chardet

class TextEncryptorDecryptor:
    """
    Класс для шифрования и дешифрования текстовых файлов с использованием динамических ключей переменной длины.
    """
    FORBIDDEN_BYTES = {
        0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25,
        0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D,
        0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D, 0x7E, 0x0D, 0x0A, 0x0B, 0x0C
    }

    def __init__(self, input_filename):
        self.input_filename = input_filename
        self.base_name = os.path.splitext(input_filename)[0]
        self.current_key_length = 1
        self.max_key_length = 5

    def generate_keys(self):
        length = 1
        while length <= self.max_key_length:
            allowed_bytes = [b for b in range(0x01, 0x100) if b not in self.FORBIDDEN_BYTES]
            for combo in product(allowed_bytes, repeat=length):
                yield bytes(combo)
            length += 1

    def get_words_and_separators(self, data):
        pattern = re.compile(
            br'([\x00-\x20\xA0\xC2\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E]|[\xC2\xA0])|([^\x00-\x20\xA0\xC2\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E\xC2\xA0]+)'
        )
        tokens = []
        for match in pattern.finditer(data):
            sep, word = match.groups()
            if sep:
                tokens.append(sep)
            elif word:
                tokens.append(word)
        return tokens

    def create_dictionary(self, tokens):
        word_counts = defaultdict(int)
        for token in tokens:
            if len(token) > 1 or (len(token) == 1 and token[0] not in self.FORBIDDEN_BYTES):
                word_counts[token] += 1
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: (-x[1], -len(x[0]), x[0])
        )
        dictionary = {}
        key_gen = self.generate_keys()
        used_keys = set()
        for word, _ in sorted_words:
            while True:
                key = next(key_gen)
                if key not in used_keys:
                    dictionary[word] = key
                    used_keys.add(key)
                    break
        return dictionary

    def encrypt_file(self, output_dtc_path, output_dict_path):
        try:
            with open(os.path.join('txt', self.input_filename), 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                logging.debug(f"Определена кодировка: {encoding}")

            with open(os.path.join('txt', self.input_filename), 'rb') as f:
                data = f.read()

            text_utf8 = data.decode(encoding).encode('utf-8')
            tokens = self.get_words_and_separators(text_utf8)
            dictionary = self.create_dictionary(tokens)

            encrypted_data = bytearray()

            for token in tokens:
                if token in dictionary:
                    encrypted_data.extend(dictionary[token])
                elif token == b'\t':
                    encrypted_data.extend(b'\x09')
                elif token == b'\n':
                    encrypted_data.extend(b'\x0A')
                elif token == b'\r\n':
                    encrypted_data.extend(b'\x0D\x0A')
                elif token == b'\xC2\xA0':
                    encrypted_data.extend(b'\xC2\xA0')
                else:
                    encrypted_data.extend(token)

            encoded_encoding = encoding.encode('utf-8')[:20].ljust(20, b'\x00')
            encrypted_data.extend(encoded_encoding)

            os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
            with open(output_dtc_path, 'wb') as f:
                f.write(encrypted_data)
            logging.info(f"Зашифрованные данные сохранены в {output_dtc_path}")

            os.makedirs(os.path.dirname(output_dict_path), exist_ok=True)
            with open(output_dict_path, 'wb') as f:
                for word, key in dictionary.items():
                    f.write(key + b' ' + word + b'\n')
            logging.info(f"Словарь сохранен в {output_dict_path}")

        except FileNotFoundError:
            logging.error(f"Файл {self.input_filename} не найден")
        except Exception as e:
            logging.error(f"Ошибка при шифровании: {str(e)}")

    def decrypt_file(self, input_dtc_path, output_path, dict_path):
        try:
            dictionary = {}
            with open(dict_path, 'rb') as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        key, word = line.split(b' ', 1)
                        dictionary[key] = word
                        # logging.debug(f"Загруженная запись из словаря (строка {line_number}): {key} -> {word}")
                    except ValueError:
                        logging.error(f"Неверный формат записи в словаре (строка {line_number}): {line}")
                        continue

            with open(input_dtc_path, 'rb') as f:
                encrypted_data = f.read()

            encoded_encoding = encrypted_data[-20:]
            try:
                encoding = encoded_encoding.rstrip(b'\x00').decode('utf-8')
            except UnicodeDecodeError as e:
                logging.error(f"Ошибка при декодировании кодировки: {str(e)}")
                return
            logging.debug(f"Извлечена кодировка: {encoding}")
            encrypted_data = encrypted_data[:-20]

            decrypted = bytearray()
            i = 0
            max_key_len = max(len(k) for k in dictionary.keys()) if dictionary else 1

            while i < len(encrypted_data):
                found = False
                for l in range(min(max_key_len, len(encrypted_data) - i), 0, -1):
                    chunk = encrypted_data[i:i + l]
                    if chunk in dictionary:
                        decrypted.extend(dictionary[chunk])
                        i += l
                        found = True
                        # logging.debug(f"Найден ключ в словаре: {chunk} -> {dictionary[chunk]}")
                        break
                if not found:
                    decrypted.extend(encrypted_data[i:i + 1])
                    i += 1
                    # logging.debug(f"Неизвестный токен: {encrypted_data[i:i + 1]}")

            try:
                decrypted_text = decrypted.decode('utf-8')
                decrypted_final = decrypted_text.encode(encoding)
                logging.debug(f"Расшифрованный текст успешно сформирован")
            except UnicodeDecodeError as e:
                logging.error(f"Ошибка при декодировании данных из UTF-8: {str(e)}")
                return

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(decrypted_final)
            logging.info(f"Дешифрованные данные сохранены в {output_path}")

        except FileNotFoundError:
            logging.error(f"Файл {input_dtc_path} или {dict_path} не найден")
        except Exception as e:
            logging.error(f"Ошибка при дешифровании: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    input_filename = 'test_utf8.txt'
    ed = TextEncryptorDecryptor(input_filename)
    ed.encrypt_file(
        os.path.join('dtc', ed.base_name + '.dtc'),
        os.path.join('dtc', ed.base_name + '.dtl')
    )
    ed.decrypt_file(
        os.path.join('dtc', ed.base_name + '.dtc'),
        os.path.join('decrypt', input_filename),
        os.path.join('dtc', ed.base_name + '.dtl')
    )
