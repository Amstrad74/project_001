import string
import struct
import json
import os

def load_word_list(filename, encoding='utf-8'):
    """
    Загружает список слов из текстового файла.

    :param filename: Имя текстового файла.
    :param encoding: Кодировка файла (по умолчанию 'utf-8').
    :return: Список слов.
    """
    try:
        with open(filename, 'r', encoding=encoding) as file:
            words = file.read().splitlines()
            return [word.strip() for word in words if word.strip()]
    except FileNotFoundError:
        print(f"Файл '{filename}' не найден.")
        return []
    except UnicodeDecodeError:
        print(f"Ошибка декодирования файла '{filename}' с кодировкой '{encoding}'. Пробуем с другой кодировкой.")
        if encoding == 'utf-8':
            try:
                with open(filename, 'r', encoding='cp1251') as file:
                    words = file.read().splitlines()
                    return [word.strip() for word in words if word.strip()]
            except Exception as e:
                print(f"Не удалось прочитать файл '{filename}': {e}")
                return []
        else:
            return []

def is_forbidden_code(code):
    """
    Проверяет, является ли код запрещённым.

    :param code: Целое число, представляющее код символа.
    :return: True, если код запрещён, иначе False.
    """
    forbidden_codes = {
        0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x7B, 0x7C, 0x7D, 0x7E
    }
    return code in forbidden_codes

def generate_hex_codes(count):
    """
    Генерирует список шестнадцатеричных кодов в порядке возрастания для заданного количества слов.

    :param count: Количество слов.
    :return: Список шестнадцатеричных кодов.
    """
    codes = []
    current = 0  # Начинаем с нулевого кода

    while len(codes) < count:
        # Преобразуем текущий код в байты
        byte_length = (current.bit_length() + 7) // 8  # Определяем необходимую длину в байтах
        byte_list = current.to_bytes(byte_length, byteorder='big')
        # Проверяем, что все байты не запрещены
        if all(not is_forbidden_code(b) for b in byte_list):
            hex_str = byte_list.hex()  # Преобразуем в шестнадцатеричную строку
            codes.append(hex_str)
            if len(codes) == count:
                break

        # Увеличиваем текущий код на 1
        current += 1
        # Проверяем, не превысили ли мы максимальное значение для текущей длины байтов
        if current.bit_length() > 32:
            raise ValueError("Количество кодов слишком велико для генерации.")

    if len(codes) < count:
        raise ValueError("Недостаточно кодов для генерации заданного количества.")

    return codes

def save_binary_library(word_list, code_list, filename):
    """
    Сохраняет слова и их шестнадцатеричные коды в бинарный файл.

    :param word_list: Список слов.
    :param code_list: Список шестнадцатеричных кодов.
    :param filename: Имя файла для сохранения.
    """
    try:
        with open(filename, 'wb') as file:
            for word, code in zip(word_list, code_list):
                # Записываем длину слова
                file.write(struct.pack('I', len(word)))
                # Записываем слово
                file.write(word.encode('utf-8'))
                # Записываем длину кода
                file.write(struct.pack('B', len(code)))
                # Записываем код
                file.write(bytes.fromhex(code))
    except IOError as e:
        print(f"Ошибка при записи в файл '{filename}': {e}")

def save_json_library(word_list, code_list, filename):
    """
    Сохраняет слова и их шестнадцатеричные коды в файл в формате JSON.

    :param word_list: Список слов.
    :param code_list: Список шестнадцатеричных кодов.
    :param filename: Имя файла для сохранения.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            # Создаем список словарей
            library = []
            for word, code in zip(word_list, code_list):
                library.append({'word': word, 'code': code})
            json.dump(library, file, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Ошибка при записи в файл '{filename}': {e}")

def main():
    # Путь к файлу word_lib.txt
    source_filename = 'word_lib.txt'

    # Путь к файлу word_lib.dtl
    binary_library_filename = 'word_lib.dtl'

    # Путь к файлу word_lib.json
    json_library_filename = 'word_lib.json'

    # Загружаем список слов
    words = load_word_list(source_filename)
    if not words:
        print("Список слов пуст или файл не найден.")
        return

    # Генерируем шестнадцатеричные коды
    codes = generate_hex_codes(len(words))

    # Сохраняем в бинарный файл
    save_binary_library(words, codes, binary_library_filename)

    # Сохраняем в JSON файл
    save_json_library(words, codes, json_library_filename)

    print(f"Библиотека успешно создана и сохранена в '{binary_library_filename}' и '{json_library_filename}'.")

if __name__ == "__main__":
    main()
