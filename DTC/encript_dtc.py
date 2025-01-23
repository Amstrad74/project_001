import string
import re
import json
from itertools import product
from decript_dtc import load_library

def split_into_words(text):
    """
    Разделяет текст на слова и разделительные символы.

    :param text: Исходный текст.
    :return: Список слов и разделительных символов.
    """
    # Шаблон для поиска слов и разделителей
    pattern = r'(\w+|[^\w\s]+|\s+)'
    return re.findall(pattern, text)

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
    tokens = split_into_words(text)
    encrypted_tokens = []
    for token in tokens:
        if re.match(r'\w+', token):
            encrypted_tokens.append(word_dict.get(token, token))
        else:
            encrypted_tokens.append(token)
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
