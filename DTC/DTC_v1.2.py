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
    # Множество запрещенных байтов, которые не могут использоваться в ключах
    FORBIDDEN_BYTES = {
        0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25,
        0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D,
        0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D, 0x7E, 0x0D, 0x0A
    }

    def __init__(self, input_filename):
        """
        Инициализация объекта шифратора/дешифратора.
        :param input_filename: Имя входного файла
        """
        self.input_filename = input_filename
        self.base_name = os.path.splitext(input_filename)[0]
        self.current_key_length = 1  # Текущая длина генерируемых ключей

    def generate_keys(self):
        """
        Генератор ключей переменной длины.
        :yield: bytes - ключ в виде байтовой строки
        """
        length = 1
        while True:
            # Генерируем все комбинации разрешенных байтов для текущей длины
            allowed_bytes = [b for b in range(0x01, 0x100) if b not in self.FORBIDDEN_BYTES]
            for combo in product(allowed_bytes, repeat=length):
                yield bytes(combo)
            length += 1  # Увеличиваем длину ключа при исчерпании комбинаций

    def get_words_and_separators(self, data):
        """
        Разделяет данные на слова и разделители.
        :param data: Исходные бинарные данные
        :return: list - список токенов (слов и разделителей)
        """
        # Регулярное выражение для разделения на слова и специальные символы
        pattern = re.compile(
            br'([^\x00-\x20]+)|([\x00-\x20])'
        )
        tokens = []
        for match in pattern.finditer(data):
            word, sep = match.groups()
            if word:
                tokens.append(word)
            elif sep:
                tokens.append(sep)
        return tokens

    def create_dictionary(self, tokens):
        """
        Создает словарь для шифрования с ключами переменной длины.
        :param tokens: Список токенов
        :return: dict - словарь {слово: ключ}
        """
        word_counts = defaultdict(int)
        # Подсчет частоты слов (исключая разделители)
        for token in tokens:
            if len(token) > 1 or (len(token) == 1 and token[0] not in self.FORBIDDEN_BYTES):
                word_counts[token] += 1
        # Сортировка слов по важности
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
        """
        Шифрует файл и сохраняет словарь.
        :param output_dtc_path: Путь для зашифрованного файла
        :param output_dict_path: Путь для файла словаря
        """
        try:
            # Определение кодировки файла
            with open(os.path.join('txt', self.input_filename), 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                logging.debug(f"Определена кодировка: {encoding}")

            # Чтение файла в бинарном режиме
            with open(os.path.join('txt', self.input_filename), 'rb') as f:
                data = f.read()

            tokens = self.get_words_and_separators(data)
            dictionary = self.create_dictionary(tokens)
            encrypted_data = bytearray()
            for token in tokens:
                if token in dictionary:
                    encrypted_data.extend(dictionary[token])
                else:
                    encrypted_data.extend(token)

            # Сохранение зашифрованных данных
            os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
            with open(output_dtc_path, 'wb') as f:
                f.write(encrypted_data)

            # Сохранение словаря
            with open(output_dict_path, 'w', encoding='utf-8') as f:
                for word, key in dictionary.items():
                    f.write(f"{key.hex()} {word.decode('utf-8')}\n")

        except Exception as e:
            print(f"Ошибка при шифровании: {str(e)}")

    def decrypt_file(self, input_dtc_path, output_path, dict_path):
        """
        Дешифрует файл с использованием словаря.
        :param input_dtc_path: Путь к зашифрованному файлу
        :param output_path: Путь для дешифрованного файла
        :param dict_path: Путь к файлу словаря
        """
        try:
            # Загрузка словаря
            dictionary = {}
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(' ', 1)
                    if len(parts) != 2:
                        continue
                    key_hex, word = parts
                    try:
                        key = bytes.fromhex(key_hex)
                        dictionary[key] = word.encode('utf-8')
                    except ValueError:
                        continue

            # Чтение зашифрованных данных
            with open(input_dtc_path, 'rb') as f:
                encrypted_data = f.read()

            # Процесс дешифровки
            decrypted = bytearray()
            i = 0
            max_key_len = max(len(k) for k in dictionary.keys()) if dictionary else 1
            while i < len(encrypted_data):
                found = False
                # Поиск самого длинного возможного ключа
                for l in range(min(max_key_len, len(encrypted_data) - i), 0, -1):
                    chunk = encrypted_data[i:i + l]
                    if chunk in dictionary:
                        decrypted.extend(dictionary[chunk])
                        i += l
                        found = True
                        break
                if not found:
                    decrypted.extend(encrypted_data[i:i + 1])
                    i += 1

            # Сохранение результата
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(decrypted)

        except Exception as e:
            print(f"Ошибка при дешифровании: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Пример использования
    input_filename = 'test_file.txt'
    ed = TextEncryptorDecryptor(input_filename)
    # Шифрование
    ed.encrypt_file(
        os.path.join('dtc', ed.base_name + '.dtc'),
        os.path.join('dtc', ed.base_name + '.dtl')
    )
    # Дешифрование
    ed.decrypt_file(
        os.path.join('dtc', ed.base_name + '.dtc'),
        os.path.join('decrypt', input_filename),
        os.path.join('dtc', ed.base_name + '.dtl')
    )
