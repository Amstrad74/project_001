import string
import re
import json
from itertools import product

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
        print(f"Файл '{filename}' не найден. Создан новый файл.")
        with open(filename, 'w', encoding=encoding) as file:
            pass
        return ""
    except UnicodeDecodeError:
        print(f"Ошибка декодирования файла '{filename}' с кодировкой '{encoding}'. Попытка с другой кодировкой.")
        if encoding == 'utf-8':
            try:
                with open(filename, 'r', encoding='cp1251') as file:
                    content = file.read()
                # Сохраняем файл в 'utf-8'
                with open(filename, 'w', encoding='utf-8') as file_utf8:
                    file_utf8.write(content)
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

def split_into_words(text):
    """
    Разделяет текст на слова и разделительные символы.

    :param text: Исходный текст.
    :return: Список слов и разделительных символов.
    """
    # Шаблон для поиска слов и разделителей
    pattern = r'(\w+|[^\w\s]+|\s+)'
    return re.findall(pattern, text)

def sanitize_text(text):
    """
    Очищает текст, сохраняя все кириллические символы, знаки препинания и специальные символы.

    :param text: Исходный текст.
    :return: Очищенный текст.
    """
    # Определяем допустимые символы:
    # - Латинские буквы в верхнем и нижнем регистре
    # - Кириллические буквы в верхнем и нижнем регистре
    # - Цифры
    # - Знаки препинания
    # - Специальные символы, включая символы ввода и переноса строки
    allowed_chars = string.ascii_letters + \
                   "".join([chr(i) for i in range(ord('А'), ord('я')+1)]) + \
                   string.digits + \
                   string.punctuation + \
                   " " + \
                   "\n" + \
                   "\r"

    # Заменяем недопустимые символы на пробел
    sanitized_text = ''.join([char if char in allowed_chars else ' ' for char in text])

    return sanitized_text

def create_word_dictionary(words):
    """
    Создает словарь слов с частотой и уникальным кодом.

    :param words: Список слов.
    :return: Словарь с кодами слов и обратный словарь для декодирования.
    """
    # Подсчитываем частоту слов
    frequency = {}
    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    # Сортируем слова по частоте (по убыванию) и по длине (по убыванию)
    sorted_words = sorted(frequency.items(), key=lambda x: (-x[1], -len(x[0])))

    # Генерируем уникальные коды
    codes = generate_codes(len(sorted_words))

    # Создаем словарь с кодами и обратный словарь для декодирования
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
        if current_length > 3:
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

def save_library(library, library_filename):
    """
    Сохраняет библиотеку слов в файл в формате JSON.

    :param library: Словарь с библиотекой слов.
    :param library_filename: Имя файла для сохранения библиотеки.
    """
    try:
        with open(library_filename, 'w', encoding='utf-8') as file:
            json.dump(library, file, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Ошибка при записи в файл библиотеки '{library_filename}': {e}")

def load_library(library_filename):
    """
    Загружает библиотеку слов из файла в формате JSON.

    :param library_filename: Имя файла библиотеки.
    :return: Словарь с библиотекой слов.
    """
    library = {}
    try:
        with open(library_filename, 'r', encoding='utf-8') as file:
            library = json.load(file)
    except FileNotFoundError:
        print(f"Файл библиотеки '{library_filename}' не найден.")
    except IOError as e:
        print(f"Ошибка при чтении файла библиотеки '{library_filename}': {e}")
    return library
