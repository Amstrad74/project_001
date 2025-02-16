import os
import re
import io
import logging
import chardet
from collections import defaultdict, deque
from itertools import product
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FileProcessor:
    """Базовый класс для обработки файлов"""

    BUFFER_SIZE = 1024 * 1024  # 1MB блоки для обработки
    MAX_MEMORY_USAGE = 1024 * 1024 * 100  # 100MB максимальное использование памяти

    def __init__(self, input_path):
        self.input_path = input_path
        self.base_name = os.path.splitext(os.path.basename(input_path))[0]
        self.lock = Lock()
        self._buffer = deque()
        self._current_memory = 0

    def _manage_memory(self, data):
        """Управление использованием памяти"""
        with self.lock:
            self._buffer.append(data)
            self._current_memory += len(data)
            while self._current_memory > self.MAX_MEMORY_USAGE:
                removed = self._buffer.popleft()
                self._current_memory -= len(removed)
                yield removed

    def stream_file(self):
        """Потоковое чтение файла с контролем памяти"""
        with open(self.input_path, "rb") as f:
            while True:
                chunk = f.read(self.BUFFER_SIZE)
                if not chunk:
                    break
                yield from self._manage_memory(chunk)
        while self._buffer:
            yield self._buffer.popleft()


class Tokenizer:
    """Класс для потоковой токенизации данных"""

    FORBIDDEN_BYTES = {
        0x00,
        0x09,
        0x20,
        0xA0,
        0xC2,
        0x21,
        0x22,
        0x23,
        0x24,
        0x25,
        0x26,
        0x27,
        0x28,
        0x29,
        0x2A,
        0x2B,
        0x2C,
        0x2D,
        0x2E,
        0x2F,
        0x3A,
        0x3B,
        0x3C,
        0x3D,
        0x3E,
        0x3F,
        0x40,
        0x5B,
        0x5C,
        0x5D,
        0x5E,
        0x5F,
        0x60,
        0x7B,
        0x7C,
        0x7D,
        0x7E,
        0x0D,
        0x0A,
        0x0B,
        0x0C,
    }

    def __init__(self):
        self._buffer = b""
        ''' Находит либо символы, которые находятся в заданных диапазонах
        (включая пробелы, специальные символы и неразрывные пробелы),
        либо последовательности символов, которые не входят в эти диапазоны.'''
        self.pattern = re.compile(
            rb"([\x00-\x20\xA0\xC2\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E]|[\xC2\xA0])|([^\x00-\x20\xA0\xC2\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E\xC2\xA0]+)"
        )

    def tokenize(self, data_chunk):
        """Потоковая токенизация данных"""
        self._buffer += data_chunk
        while True:
            match = self.pattern.search(self._buffer)
            if not match:
                break
            start, end = match.span()
            if start > 0:
                yield self._buffer[:start], False
            yield match.group(), True
            self._buffer = self._buffer[end:]
        if self._buffer:
            yield self._buffer, False
            self._buffer = b""


class DictionaryManager:
    """Управление словарем с использованием хеширования"""

    def __init__(self):
        self.dictionary = {}
        self.reverse_dict = {}
        self.key_generator = self._key_generator()
        self.lock = Lock()

    def _key_generator(self):
        """Генератор ключей с переменной длиной"""
        length = 1
        while True:
            allowed_bytes = [
                b for b in range(0x01, 0x100) if b not in Tokenizer.FORBIDDEN_BYTES
            ]
            for combo in product(allowed_bytes, repeat=length):
                yield bytes(combo)
            length += 1

    def add_token(self, token):
        """Потокобезопасное добавление токена в словарь"""
        with self.lock:
            if token not in self.dictionary:
                key = next(self.key_generator)
                self.dictionary[token] = key
                self.reverse_dict[key] = token
            return self.dictionary[token]


class Encryptor(FileProcessor):
    """Класс для потокового шифрования файлов"""

    def __init__(self, input_path):
        super().__init__(input_path)
        self.tokenizer = Tokenizer()
        self.dict_manager = DictionaryManager()
        self.encoding = "utf-8"

    def _detect_encoding(self):
        """Определение кодировки первых 1MB данных"""
        with open(self.input_path, "rb") as f:
            raw_data = f.read(1024 * 1024)
            result = chardet.detect(raw_data)
            self.encoding = result["encoding"] or "utf-8"
            logging.info(f"Определена кодировка: {self.encoding}")

    def encrypt(self, output_dtc_path, output_dict_path):
        """Основной метод шифрования"""
        self._detect_encoding()
        buffer = io.BytesIO()

        with ThreadPoolExecutor() as executor:
            futures = []
            for chunk in self.stream_file():
                futures.append(executor.submit(self.process_chunk, chunk))

            for future in futures:
                encrypted_chunk = future.result()
                buffer.write(encrypted_chunk)

        # Добавление информации о кодировке
        encoded_encoding = self.encoding.encode("utf-8")[:20].ljust(20, b"\x00")
        buffer.write(encoded_encoding)

        # Сохранение результатов
        os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
        with open(output_dtc_path, "wb") as f:
            f.write(buffer.getvalue())

        self.save_dictionary(output_dict_path)
        logging.info(f"Файл успешно зашифрован: {output_dtc_path}")

    def process_chunk(self, chunk):
        """Обработка чанка данных"""
        encrypted = bytearray()
        try:
            decoded_chunk = chunk.decode(self.encoding).encode("utf-8")
            for token, is_separator in self.tokenizer.tokenize(decoded_chunk):
                if is_separator:
                    encrypted.extend(token)
                else:
                    key = self.dict_manager.add_token(token)
                    encrypted.extend(key)
        except UnicodeDecodeError:
            logging.warning("Ошибка декодирования чанка, используются сырые байты")
            encrypted.extend(chunk)
        return bytes(encrypted)

    def save_dictionary(self, output_path):
        """Сохранение словаря с использованием потоковой записи"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            for token, key in self.dict_manager.dictionary.items():
                f.write(key + b" " + token + b"\n")


class Decryptor(FileProcessor):
    """Класс для потокового дешифрования файлов"""

    def __init__(self, input_path):
        super().__init__(input_path)
        self.dictionary = {}
        self.encoding = "utf-8"

    def load_dictionary(self, dict_path):
        """Загрузка словаря с проверкой целостности"""
        with open(dict_path, "rb") as f:
            for line in f:
                parts = line.strip().split(b" ", 1)
                if len(parts) == 2:
                    key, value = parts
                    self.dictionary[key] = value
        logging.info(f"Загружено записей в словаре: {len(self.dictionary)}")

    def decrypt(self, output_path, dict_path):
        """Основной метод дешифрования"""
        self.load_dictionary(dict_path)
        buffer = io.BytesIO()

        with ThreadPoolExecutor() as executor:
            futures = []
            for chunk in self.stream_file():
                futures.append(executor.submit(self.process_chunk, chunk))

            for future in futures:
                decrypted_chunk = future.result()
                buffer.write(decrypted_chunk)

        # Извлечение информации о кодировке
        data = buffer.getvalue()
        encoded_encoding = data[-20:]
        self.encoding = (
            encoded_encoding.rstrip(b"\x00").decode("utf-8", errors="ignore") or "utf-8"
        )
        data = data[:-20]

        # Сохранение результатов
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            try:
                decoded = data.decode("utf-8").encode(self.encoding)
                f.write(decoded)
            except UnicodeEncodeError:
                f.write(data)
                logging.error("Ошибка конвертации кодировки, сохранены сырые данные")

        logging.info(f"Файл успешно дешифрован: {output_path}")

    def process_chunk(self, chunk):
        """Обработка чанка данных"""
        decrypted = bytearray()
        i = 0
        max_key_len = (
            max(len(k) for k in self.dictionary.keys()) if self.dictionary else 1
        )

        while i < len(chunk):
            found = False
            for l in range(min(max_key_len, len(chunk) - i), 0, -1):
                key = chunk[i : i + l]
                if key in self.dictionary:
                    decrypted.extend(self.dictionary[key])
                    i += l
                    found = True
                    break
            if not found:
                decrypted.extend(chunk[i : i + 1])
                i += 1

        return bytes(decrypted)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    input_filename = 'test3.txt'
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


if __name__ == "__main__":
    input_file = os.path.join("txt", "test_file.txt")

    # Шифрование
    encryptor = Encryptor(input_file)
    encryptor.encrypt(
        os.path.join("dtc", "encrypted.dtc"), os.path.join("dtc", "dictionary.dtl")
    )

    # Дешифрование
    decryptor = Decryptor(os.path.join("dtc", "encrypted.dtc"))
    decryptor.decrypt(
        os.path.join("decrypt", "large_file.txt"),
        os.path.join("dtc", "dictionary.dtl"),
    )
