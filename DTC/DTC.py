import string
import re
from itertools import product
import json
import os

def load_file(filename, encoding='utf-8'):
    """
    Загружает содержимое текстового файла в строку с учетом кодировки.

    :param filename: Имя текстового файла.
    :param encoding: Кодировка файла (по умолчанию 'utf-8').
    :return: Строка с содержимым файла.
    """
    try:
        with open(filename, 'r', encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        print(f"Файл '{filename}' не найден.")
        return ""
    except UnicodeDecodeError:
        print(f"Ошибка декодирования файла '{filename}' с кодировкой '{encoding}'. Попытка с другой кодировкой.")
        if encoding == 'utf-8':
            try:
                with open(filename, 'r', encoding='cp1251') as file:
                    content = file.read()
                return content
            except Exception as e:
                print(f"Не удалось прочитать файл '{filename}': {e}")
                return ""
        else:
            return ""
    except IOError as e:
        print(f"Ошибка при чтении файла '{filename}': {e}")
        return ""

def save_file(filename, content, encoding='utf-8'):
    """
    Сохраняет содержимое в текстовый файл с указанной кодировкой.

    :param filename: Имя файла для сохранения.
    :param content: Строка с содержимым для сохранения.
    :param encoding: Кодировка для сохранения (по умолчанию 'utf-8').
    """
    try:
        with open(filename, 'w', encoding=encoding) as file:
            file.write(content)
    except IOError as e:
        print(f"Ошибка при записи в файл '{filename}': {e}")

def sanitize_text(text):
    """
    Очищает текст, сохраняя все кириллические и латинские символы, а также знаки препинания.

    :param text: Исходный текст.
    :return: Очищенный текст.
    """
    allowed_chars = string.ascii_letters + "".join([chr(i) for i in range(ord('А'), ord('я')+1)]) + string.punctuation + " " + "\n" + "\r"
    sanitized_text = ''.join([char if char in allowed_chars else ' ' for char in text])
    return sanitized_text

def split_into_words(text):
    """
    Разделяет текст на слова и разделительные символы.

    :param text: Исходный текст.
    :return: Список слов и разделительных символов.
    """
    pattern = r'(\w+|[^\w\s]+|\s+)'
    return re.findall(pattern, text)

def create_word_dictionary(words):
    """
    Создает словарь слов с частотой и уникальным кодом.

    :param words: Список слов.
    :return: Словарь с кодами слов и обратный словарь для декодирования.
    """
    frequency = {}
    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    # Сортируем слова по частоте (по убыванию) и по длине (по возрастанию)
    sorted_words = sorted(frequency.items(), key=lambda x: (-x[1], len(x[0])))

    codes = generate_codes(len(sorted_words))

    word_dict = {}
    reverse_dict = {}
    for i, (word, freq) in enumerate(sorted_words):
        word_dict[word] = codes[i]
        reverse_dict[codes[i]] = word

    return word_dict, reverse_dict

def generate_codes(count):
    """
    Генерирует уникальные коды без ведущих нулей.

    :param count: Количество необходимых кодов.
    :return: Список уникальных кодов.
    """
    codes = set()
    current_length = 1
    while len(codes) < count:
        if current_length > 4:
            current_length += 1
            continue
        alphabet = string.ascii_letters + string.digits
        possible_codes = [''.join(p) for p in product(alphabet, repeat=current_length)]
        for code in possible_codes:
            if code not in codes:
                codes.add(code)
                if len(codes) == count:
                    break
        current_length += 1

    return list(codes)

def encrypt_text(text, word_dict):
    """
    Зашифровывает текст, используя словарь слов.

    :param text: Исходный текст.
    :param word_dict: Словарь с кодами слов.
    :return: Зашифрованная строка.
    """
    tokens = split_into_words(sanitize_text(text))
    encrypted_tokens = [word_dict.get(token.strip(), token) for token in tokens]
    return ' '.join(encrypted_tokens)

def save_file(filename, content, encoding='utf-8'):
    """
    Сохраняет содержимое в текстовый файл с указанной кодировкой.

    :param filename: Имя файла для сохранения.
    :param content: Строка с содержимым для сохранения.
    :param encoding: Кодировка для сохранения (по умолчанию 'utf-8').
    """
    try:
        with open(filename, 'w', encoding=encoding) as file:
            file.write(content)
    except IOError as e:
        print(f"Ошибка при записи в файл '{filename}': {e}")

def encrypt_file(input_filename, output_filename, library_filename):
    """
    Шифрует файл, используя библиотеку слов.

    :param input_filename: Имя входного файла.
    :param output_filename: Имя выходного файла.
    :param library_filename: Имя файла библиотеки.
    """
    library = load_library(library_filename)
    text = load_file(input_filename)
    encrypted_text = encrypt_text(text, library)
    save_file(output_filename, encrypted_text)

def decrypt_file(input_filename, output_filename, library_filename):
    """
    Расшифровывает файл, используя библиотеку слов.

    :param input_filename: Имя входного зашифрованного файла.
    :param output_filename: Имя выходного файла для сохранения расшифрованного текста.
    :param library_filename: Имя файла библиотеки.
    """
    library = load_library(library_filename)
    reverse_dict = {code: word for word, code in library.items()}
    text = load_file(input_filename)
    decrypted_text = decrypt_text(text, reverse_dict)
    save_file(output_filename, decrypted_text)

def process_folder(folder_path, operation='encrypt', library_filename='word_lib.json'):
    """
    Обрабатывает все файлы в указанной папке, шифруя или расшифровывая их.

    :param folder_path: Путь к папке с файлами.
    :param operation: Операция для выполнения - 'encrypt' для шифрования, 'decrypt' для расшифровки.
    :param library_filename: Имя файла библиотеки.
    """
    if operation == 'encrypt':
        dtc_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dtc')
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                input_path = os.path.join(folder_path, filename)
                base_name = os.path.splitext(filename)[0]
                output_filename = f"{base_name}.dtc"
                output_path = os.path.join(dtc_folder, output_filename)
                encrypt_file(input_path, output_path, library_filename)
    elif operation == 'decrypt':
        decript_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decript')
        for filename in os.listdir(folder_path):
            if filename.endswith('.dtc'):
                input_path = os.path.join(folder_path, filename)
                base_name = os.path.splitext(filename)[0]
                output_filename = f"{base_name}.txt"
                output_path = os.path.join(decript_folder, output_filename)
                decrypt_file(input_path, output_path, library_filename)
    else:
        print("Неверная операция. Используйте 'encrypt' или 'decrypt'.")

def verify_files(original_folder, decrypted_folder):
    """
    Проверяет, совпадают ли оригинальные и расшифрованные файлы.

    :param original_folder: Путь к папке с оригинальными файлами.
    :param decrypted_folder: Путь к папке с расшифрованными файлами.
    :return: True, если все файлы совпадают, иначе False.
    """
    for filename in os.listdir(original_folder):
        if filename.endswith('.txt'):
            original_path = os.path.join(original_folder, filename)
            decrypted_path = os.path.join(decrypted_folder, filename)
            if not os.path.exists(decrypted_path):
                print(f"Файл '{decrypted_path}' не найден.")
                return False
            with open(original_path, 'r', encoding='utf-8') as original_file, open(decrypted_path, 'r', encoding='utf-8') as decrypted_file:
                original_content = original_file.read()
                decrypted_content = decrypted_file.read()
                if original_content != decrypted_content:
                    print(f"Файл '{filename}' не совпадает с расшифрованным файлом.")
                    return False
    return True

def main():
    # Путь к папке с исходными текстовыми файлами
    txt_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'txt')

    # Путь к папке для зашифрованных файлов
    dtc_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dtc')

    # Путь к папке для расшифрованных файлов
    decript_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decript')

    # Путь к файлу библиотеки
    library_filename = 'word_lib.json'

    # Создание папок, если они не существуют
    for folder in [dtc_folder, decript_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Создание библиотеки слов, если она не существует
    if not os.path.exists(library_filename):
        # Создаем новую библиотеку
        print("Создание новой библиотеки слов.")
        txt_files = [os.path.join(txt_folder, f) for f in os.listdir(txt_folder) if f.endswith('.txt')]
        all_text = ''
        for file in txt_files:
            all_text += load_file(file) + ' '
        words = split_into_words(sanitize_text(all_text))
        word_dict, reverse_dict = create_word_dictionary(words)
        save_library(word_dict, library_filename)

    # Шифрование файлов
    process_folder(txt_folder, operation='encrypt', library_filename=library_filename)

    # Расшифровка файлов
    process_folder(dtc_folder, operation='decrypt', library_filename=library_filename)

    # Проверка совпадения оригинальных и расшифрованных файлов
    if verify_files(txt_folder, decript_folder):
        print("Все файлы совпадают с оригиналами.")
    else:
        print("Ошибка: файлы не совпадают.")

if __name__ == "__main__":
    main()
