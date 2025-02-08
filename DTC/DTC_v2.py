# Не рабочая

import os
import re
from collections import defaultdict

class TextEncryptorDecryptor:
    # Обновленный список запрещенных байтов (добавлен 0xC2)
    FORBIDDEN_BYTES = {
        0x00, 0x09, 0x20, 0xA0, 0xC2, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
        0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x3A, 0x3B, 0x3C, 0x3D,
        0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D,
        0x7E, 0x0D, 0x0A
    }

    def __init__(self, input_filename, input_folder='txt', output_dtc_folder='dtc', output_dict_folder='dtc', decrypt_folder='decrypt'):
        self.input_filename = input_filename
        self.base_name = os.path.splitext(input_filename)[0]
        self.input_folder = input_folder
        self.output_dtc_folder = output_dtc_folder
        self.output_dict_folder = output_dict_folder
        self.decrypt_folder = decrypt_folder

    def is_forbidden_code(self, code):
        """
        Проверяет, является ли код запрещённым.

        :param code: Целое число, представляющее код символа.
        :return: True, если код запрещён, иначе False.
        """
        return code in self.FORBIDDEN_BYTES

    def generate_hex_codes(self, count):
        """
        Генерирует список шестнадцатеричных кодов в порядке возрастания для заданного количества слов.

        :param count: Количество слов.
        :return: Список шестнадцатеричных кодов.
        """
        codes = []
        current = 1  # Начинаем с кода 1

        while len(codes) < count:
            # Преобразуем текущий код в байты
            byte_length = (current.bit_length() + 7) // 8  # Определяем необходимую длину в байтах
            byte_list = current.to_bytes(byte_length, byteorder='big')
            # Проверяем, что все байты не запрещены
            if all(not self.is_forbidden_code(b) for b in byte_list):
                hex_str = byte_list.hex()  # Преобразуем в шестнадцатеричную строку
                codes.append(hex_str)
                if len(codes) == count:
                    break

            # Увеличиваем текущий код на 1
            current += 1
            # Проверяем, не превысили ли мы максимальное значение для 4 байтов
            if current.bit_length() > 32:
                raise ValueError("Количество кодов слишком велико для генерации.")

        if len(codes) < count:
            raise ValueError("Недостаточно кодов для генерации заданного количества.")

        return codes

    def get_words_and_separators(self, text):
        """
        Разбивает текст на слова и разделители.

        :param text: Входной текст.
        :return: Список токенов (слов и разделителей).
        """
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

    def create_dictionary(self, tokens):
        """
        Создает словарь для шифрования.

        :param tokens: Список токенов.
        :return: Словарь, где ключи - слова, значения - байты.
        """
        word_counts = defaultdict(int)
        for token in tokens:
            if len(token) > 1 or (len(token) == 1 and ord(token[0]) not in self.FORBIDDEN_BYTES):
                word_counts[token] += 1
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: (-x[1], -len(x[0]), x[0])
        )
        count = len(sorted_words)
        codes = self.generate_hex_codes(count)
        dictionary = {}
        for word, code_hex in zip(sorted_words, codes):
            dictionary[word] = bytes.fromhex(code_hex)
        return dictionary

    def encrypt_file(self, output_dtc_path, output_dict_path):
        """
        Шифрует файл и создает словарь.

        :param output_dtc_path: Путь к зашифрованному файлу.
        :param output_dict_path: Путь к словарю.
        """
        try:
            with open(os.path.join(self.input_folder, self.input_filename), 'rb') as f:
                text = f.read()
            tokens = self.get_words_and_separators(text.decode('utf-8'))
            dictionary = self.create_dictionary(tokens)
            encrypted_data = bytearray()
            for token in tokens:
                if token in dictionary:
                    encrypted_data.extend(dictionary[token])
                else:
                    encrypted_data.extend(token.encode('utf-8'))
            os.makedirs(os.path.dirname(output_dtc_path), exist_ok=True)
            with open(output_dtc_path, 'wb') as f:
                f.write(encrypted_data)
            with open(output_dict_path, 'w', encoding='utf-8') as f:
                for word, key in dictionary.items():
                    f.write(f"{key.hex()} {word}\n")
        except Exception as e:
            print(f"Ошибка при шифровании: {e}")

    def decrypt_file(self, input_dtc_path, output_path, dict_path):
        """
        Дешифрует файл с использованием словаря.

        :param input_dtc_path: Путь к зашифрованному файлу.
        :param output_path: Путь к дешифрованному файлу.
        :param dict_path: Путь к словарю.
        """
        try:
            print("Начало дешифрования...")
            dictionary = {}
            print(f"Чтение словаря из {dict_path}...")
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2:
                        key_hex, word = parts
                        try:
                            key = bytes.fromhex(key_hex)
                            dictionary[key] = word
                            print(f"Добавлен ключ: {key_hex} -> {word}")
                        except ValueError:
                            print(f"Некорректный ключ: {key_hex}")
                            continue
            print(f"Количество ключей в словаре: {len(dictionary)}")
            print(f"Чтение зашифрованных данных из {input_dtc_path}...")
            with open(input_dtc_path, 'rb') as f:
                encrypted_data = f.read()
            print(f"Размер зашифрованных данных: {len(encrypted_data)} байт")
            decrypted = []
            i = 0
            while i < len(encrypted_data):
                byte_chunk = encrypted_data[i:i + 4]
                if len(byte_chunk) == 4:
                    key = int.from_bytes(byte_chunk, byteorder='big')
                    if key in dictionary:
                        decrypted.append(dictionary[key])
                        i += 4
                        continue
                byte = encrypted_data[i:i + 1]
                if byte in dictionary:
                    decrypted.append(dictionary[byte])
                    i += 1
                else:
                    try:
                        char = encrypted_data[i:i + 1].decode('utf-8')
                        decrypted.append(char)
                        i += 1
                    except UnicodeDecodeError:
                        try:
                            char = encrypted_data[i:i + 2].decode('utf-8')
                            decrypted.append(char)
                            i += 2
                        except:
                            decrypted.append('\uFFFD')  # Символ замены
                            i += 1
            print("Дешифрование завершено.")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                f.write(''.join(decrypted))
            print(f"Дешифрованный файл сохранен: {output_path}")
        except Exception as e:
            print(f"Ошибка при дешифровании: {e}")

if __name__ == "__main__":
    input_filename = 'test_file1.txt'
    encryptor_decryptor = TextEncryptorDecryptor(input_filename)
    # Шифрование
    encryptor_decryptor.encrypt_file(
        os.path.join('dtc', encryptor_decryptor.base_name + '.dtc'),
        os.path.join('dtc', encryptor_decryptor.base_name + '.dtl')
    )
    # Дешифрование
    decrypt_path = os.path.join('decrypt', input_filename)
    dict_path = os.path.join('dtc', encryptor_decryptor.base_name + '.dtl')
    encryptor_decryptor.decrypt_file(
        os.path.join('dtc', encryptor_decryptor.base_name + '.dtc'),
        decrypt_path,
        dict_path
    )