import os
import re
import logging
import chardet
from collections import defaultdict
from itertools import product

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class TextEncryptorDecryptor:
    """
    Версия дипфинка 1.1 с поддержкой любых кодировок
    глючная, с удалённым блоком спецсимволов

    Основные изменения:
    1. Автоматическое определение кодировки исходного файла
    2. Конвертация в UTF-8 для обработки
    3. Сохранение исходной кодировки в конце файла
    4. Обратная конвертация при дешифровании
    """

    FORBIDDEN_BYTES = {
        0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25,
        0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D,
        0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D, 0x7E, 0x0D, 0x0A
    }
    ENCODING_MARKER = b'ENCv1.2|'  # 8 байт для маркера
    ENCODING_LENGTH = 20  # Общая длина блока с кодировкой

    def __init__(self, input_filename):
        self.input_filename = input_filename
        self.base_name = os.path.splitext(input_filename)[0]
        self.original_encoding = 'utf-8'

    def generate_keys(self):
        """Генератор ключей переменной длины"""
        length = 1
        while True:
            allowed_bytes = [b for b in range(0x01, 0x100) if b not in self.FORBIDDEN_BYTES]
            for combo in product(allowed_bytes, repeat=length):
                yield bytes(combo)
            length += 1

    def get_words_and_separators(self, text):
        """Разделение текста на токены с логированием"""
        pattern = re.compile(r'([^\x00-\x20\x7F-\xA0]+)|([\x00-\x20\x7F-\xA0])', re.UNICODE)
        tokens = []
        for match in pattern.finditer(text):
            word, sep = match.groups()
            tokens.append(word if word else sep)
        logging.debug(f"Выделено {len(tokens)} токенов")
        return tokens

    def create_dictionary(self, tokens):
        """Создание словаря с проверкой уникальности ключей"""
        word_counts = defaultdict(int)
        for token in tokens:
            if len(token) > 1 or (len(token) == 1 and ord(token[0]) not in self.FORBIDDEN_BYTES):
                word_counts[token] += 1
        logging.debug(f"Уникальных слов для словаря: {len(word_counts)}")

        sorted_words = sorted(word_counts.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))

        dictionary = {}
        key_gen = self.generate_keys()
        used_keys = set()

        for word, _ in sorted_words:
            while True:
                key = next(key_gen)
                if key not in used_keys and not any(b in self.FORBIDDEN_BYTES for b in key):
                    dictionary[word] = key
                    used_keys.add(key)
                    break
        return dictionary

    def encrypt_file(self, output_dtc_path, output_dict_path):
        """Улучшенное шифрование с поддержкой кодировок"""
        try:
            # Чтение и определение кодировки
            input_path = os.path.join('txt', self.input_filename)
            with open(input_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                self.original_encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
                logging.debug(f"Определена кодировка: {self.original_encoding}")

            # Конвертация в UTF-8
            try:
                text = raw_data.decode(self.original_encoding)
            except UnicodeDecodeError:
                text = raw_data.decode('utf-8', errors='replace')
                logging.warning("Ошибка декодирования, использован utf-8 с заменой символов")

            # Основной процесс шифрования
            tokens = self.get_words_and_separators(text)
            dictionary = self.create_dictionary(tokens)

            encrypted_data = bytearray()
            for token in tokens:
                encrypted_data.extend(dictionary.get(token, token.encode('utf-8')))

            # Добавление метаданных о кодировке
            encoding_info = self.ENCODING_MARKER + self.original_encoding.encode('utf-8').ljust(12)
            encrypted_data.extend(encoding_info)

            # Сохранение результатов
            os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
            with open(output_dtc_path, 'wb') as f:
                f.write(encrypted_data)
                logging.info(f"Файл {output_dtc_path} успешно зашифрован")

            with open(output_dict_path, 'w', encoding='utf-8') as f:
                for word, key in dictionary.items():
                    f.write(f"{key.hex()} {word}\n")
                logging.info(f"Словарь {output_dict_path} успешно создан")

        except Exception as e:
            logging.error(f"Ошибка шифрования: {str(e)}", exc_info=True)

    def decrypt_file(self, input_dtc_path, output_path, dict_path):
        """Дешифрование с восстановлением кодировки"""
        try:
            # Чтение зашифрованных данных
            with open(input_dtc_path, 'rb') as f:
                encrypted_data = f.read()

            # Извлечение информации о кодировке
            encoding_info = encrypted_data[-self.ENCODING_LENGTH:]
            if encoding_info.startswith(self.ENCODING_MARKER):
                self.original_encoding = encoding_info[len(self.ENCODING_MARKER):].decode('utf-8').strip()
                encrypted_data = encrypted_data[:-self.ENCODING_LENGTH]
                logging.debug(f"Восстановлена кодировка: {self.original_encoding}")
            else:
                self.original_encoding = 'utf-8'
                logging.warning("Маркер кодировки не найден, используется utf-8")

            # Загрузка словаря
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

            # Процесс дешифровки
            decrypted = []
            i = 0
            max_key_len = max(len(k) for k in dictionary.keys()) if dictionary else 1

            while i < len(encrypted_data):
                found = False
                for l in range(min(max_key_len, len(encrypted_data) - i), 0, -1):
                    chunk = encrypted_data[i:i + l]
                    if chunk in dictionary:
                        decrypted.append(dictionary[chunk])
                        i += l
                        found = True
                        break
                if not found:
                    try:
                        decrypted.append(encrypted_data[i:i + 1].decode('utf-8'))
                    except UnicodeDecodeError:
                        decrypted.append('\uFFFD')
                    i += 1

            # Конвертация в исходную кодировку
            try:
                result = ''.join(decrypted).encode('utf-8').decode(self.original_encoding)
            except UnicodeEncodeError:
                result = ''.join(decrypted)
                logging.error("Ошибка конвертации в исходную кодировку")

            # Сохранение результата
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding=self.original_encoding, errors='replace') as f:
                f.write(result)
                logging.info(f"Файл {output_path} успешно дешифрован")

        except Exception as e:
            logging.error(f"Ошибка дешифрования: {str(e)}", exc_info=True)


if __name__ == "__main__":
    # Тестовые данные
    test_file = 'test_file.txt'  # имя входящего файла

    # Инициализация обработчика
    processor = TextEncryptorDecryptor(test_file)

    # Шифрование
    processor.encrypt_file(
        os.path.join('dtc', f"{processor.base_name}.dtc"),
        os.path.join('dtc', f"{processor.base_name}.dtl")
    )

    # Дешифрование
    processor.decrypt_file(
        os.path.join('dtc', f"{processor.base_name}.dtc"),
        os.path.join('decrypt', test_file),
        os.path.join('dtc', f"{processor.base_name}.dtl")
    )
