import os
import re
import zipfile
import chardet
import xml.etree.ElementTree as ET
from collections import defaultdict
from itertools import product


class AdvancedFileProcessor:
    """
    Версия 1.1 с поддержкой структурированных форматов
    и автоматическим определением кодировки
    """

    FORBIDDEN_BYTES = {
        0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25,
        0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D,
        0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D, 0x7E, 0x0D, 0x0A
    }

    def __init__(self, input_filename):
        self.input_filename = input_filename
        self.base_name = os.path.splitext(input_filename)[0]
        self.encoding = 'utf-8'
        self.is_binary = False

    def detect_encoding(self, data):
        """Определение кодировки текста"""
        try:
            result = chardet.detect(data)
            if result['confidence'] > 0.7:
                return result['encoding']
            return 'utf-8'
        except:
            return 'utf-8'

    def process_fb2(self, data):
        """Обработка FB2 файлов"""
        try:
            root = ET.fromstring(data)
            # Обработка текстовых узлов
            for elem in root.iter():
                if elem.text and elem.tag.endswith('}section'):
                    yield ('text', elem.text)
                elif elem.tag.endswith('}binary'):
                    yield ('binary', (elem.attrib['id'], elem.text))
            return 'fb2'
        except ET.ParseError:
            return 'txt'

    def process_docx(self, file_path):
        """Обработка DOCX файлов"""
        with zipfile.ZipFile(file_path) as z:
            for name in z.namelist():
                if name.startswith('word/') and name.endswith('.xml'):
                    with z.open(name) as f:
                        content = f.read()
                        yield ('text', content.decode('utf-8'))
                else:
                    with z.open(name) as f:
                        yield ('binary', (name, f.read()))

    def generate_keys(self):
        allowed_bytes = [b for b in range(0x01, 0x100) if b not in self.FORBIDDEN_BYTES]
        length = 1
        while True:
            for combo in product(allowed_bytes, repeat=length):
                yield bytes(combo)
            length += 1

    def create_dictionary(self, tokens):
        word_counts = defaultdict(int)
        for token in tokens:
            if len(token) > 1 or (len(token) == 1 and ord(token[0]) not in self.FORBIDDEN_BYTES):
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
        """Шифрование файла с учетом структуры"""
        try:
            input_path = os.path.join('txt', self.input_filename)
            file_ext = os.path.splitext(self.input_filename)[1].lower()

            encrypted_data = bytearray()
            dictionaries = []

            # Обработка DOCX
            if file_ext == '.docx':
                for content_type, content in self.process_docx(input_path):
                    if content_type == 'text':
                        tokens = re.findall(r'\w+|\W+', content)
                        dictionary = self.create_dictionary(tokens)
                        for token in tokens:
                            encrypted_data.extend(dictionary.get(token, token.encode('utf-8')))
                        dictionaries.append(dictionary)
                    else:
                        encrypted_data.extend(f"BIN:{content[0]}:".encode() + content[1])

            # Обработка FB2 и других текстовых форматов
            else:
                with open(input_path, 'rb') as f:
                    raw_data = f.read()
                    self.encoding = self.detect_encoding(raw_data)

                try:
                    data = raw_data.decode(self.encoding)
                except UnicodeDecodeError:
                    data = raw_data.decode('utf-8', errors='replace')
                    print(f"Внимание: Файл {self.input_filename} содержит некорректные символы!")

                if file_ext == '.fb2':
                    file_type = self.process_fb2(data.encode('utf-8'))
                    for content_type, content in self.process_fb2(data.encode('utf-8')):
                        if content_type == 'text':
                            tokens = re.findall(r'\w+|\W+', content)
                            dictionary = self.create_dictionary(tokens)
                            for token in tokens:
                                encrypted_data.extend(dictionary.get(token, token.encode('utf-8')))
                            dictionaries.append(dictionary)
                        else:
                            encrypted_data.extend(f"BIN:{content[0]}:".encode() + content[1].encode())
                else:
                    tokens = re.findall(r'\w+|\W+', data)
                    dictionary = self.create_dictionary(tokens)
                    for token in tokens:
                        encrypted_data.extend(dictionary.get(token, token.encode(self.encoding)))
                    dictionaries.append(dictionary)

            # Сохранение данных
            os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
            with open(output_dtc_path, 'wb') as f:
                f.write(encrypted_data)

            # Сохранение объединенного словаря
            merged_dict = {}
            for d in dictionaries:
                merged_dict.update(d)

            with open(output_dict_path, 'w', encoding='utf-8') as f:
                for word, key in merged_dict.items():
                    f.write(f"{key.hex()} {word}\n")
                f.write(f"ENCODING:{self.encoding}\n")

        except Exception as e:
            print(f"Ошибка при шифровании: {str(e)}")

    def decrypt_file(self, input_dtc_path, output_path, dict_path):
        """Дешифрование файла"""
        try:
            # Загрузка словаря и информации о кодировке
            dictionary = {}
            encoding = 'utf-8'
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ENCODING:'):
                        encoding = line.split(':')[1].strip()
                        continue
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        key_hex, word = parts
                        try:
                            key = bytes.fromhex(key_hex)
                            dictionary[key] = word
                        except ValueError:
                            continue

            with open(input_dtc_path, 'rb') as f:
                encrypted_data = f.read()

            result = bytearray()
            i = 0
            max_key_len = max(len(k) for k in dictionary.keys()) if dictionary else 1

            while i < len(encrypted_data):
                # Обработка бинарных блоков
                if encrypted_data[i:i+4] == b'BIN:':
                    end_marker = encrypted_data.find(b':', i + 4)
                    name = encrypted_data[i + 4:end_marker].decode()
                    i = end_marker + 1
                    size = int.from_bytes(encrypted_data[i:i + 4], 'big')
                    i += 4
                    result.extend(encrypted_data[i:i + size])
                    i += size
                    continue

                # Дешифровка текста
                found = False
                for l in range(min(max_key_len, len(encrypted_data) - i), 0, -1):
                    chunk = encrypted_data[i:i + l]
                    if chunk in dictionary:
                        result.extend(dictionary[chunk].encode(encoding))
                        i += l
                        found = True
                        break
                if not found:
                    result.extend(encrypted_data[i:i + 1])
                    i += 1

            # Восстановление структуры DOCX
            if output_path.endswith('.docx'):
                with zipfile.ZipFile(output_path, 'w') as z:
                    # Здесь должна быть логика восстановления структуры архива
                    pass
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(result)

        except Exception as e:
            print(f"Ошибка при дешифровании: {str(e)}")


if __name__ == "__main__":
    input_filename = 'test_txt.txt'
    processor = AdvancedFileProcessor(input_filename)

    # Шифрование
    processor.encrypt_file(
        os.path.join('dtc', processor.base_name + '.dtc'),
        os.path.join('dtc', processor.base_name + '.dtl')
    )

    # Дешифрование
    processor.decrypt_file(
        os.path.join('dtc', processor.base_name + '.dtc'),
        os.path.join('decript', input_filename),
        os.path.join('dtc', processor.base_name + '.dtl')
    )
