import string
import random
import os
import re
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
    Разбивает текст на слова и знаки препинания.

    :param text: Строка с текстом.
    :return: Список слов и знаков препинания.
    """
    # Используем регулярное выражение для разделения текста на слова и знаки препинания
    tokens = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    return tokens

def sanitize_text(text):
    """
    Очищает текст от недопустимых символов и заменяет их на '#', корректно обрабатывает переносы строк, дефисы, тире и знаки препинания.

    :param text: Исходный текст.
    :return: Очищенный текст.
    """

    # Сначала заменяем символы переноса строки и ввода
    text = text.replace('\n', '|').replace('\r', '|')

    # Определяем допустимые символы:
    # - Латинские буквы в верхнем и нижнем регистре
    # - Кириллические буквы в верхнем и нижнем регистре
    # - Цифры
    # - Знаки препинания, включая дефис и тире
    # - Пробел
    allowed_chars = string.ascii_letters + \
                   "".join([chr(i) for i in range(ord('А'), ord('я')+1)]) + \
                   string.digits + \
                   " " + '|' + \
                   "".join([chr(i) for i in range(ord('!'), ord('~')+1)])  # Включаем символы от пробела до '~'

    # Заменяем недопустимые символы на '#'
    sanitized_text = ''.join([char if char in allowed_chars else '#' for char in text])

    # Удаляем лишние пробелы вокруг знаков препинания
    # Определяем знаки препинания, которые должны быть впритык к слову
    punctuation = string.punctuation.replace('-', '')  # Убираем дефис, чтобы он не удалялся
    for p in punctuation:
        # Заменяем ' p' на 'p' и 'p ' на 'p'
        sanitized_text = sanitized_text.replace(f' {p}', p).replace(f'{p} ', p)

    # Обрабатываем дефисы и тире
    # Заменяем длинное тире на короткое
    sanitized_text = sanitized_text.replace('—', '-').replace('–', '-')

    return sanitized_text

def create_word_dictionary(words, library):
    """
    Создает словарь слов с частотой и уникальным кодом, используя существующую библиотеку.

    :param words: Список слов.
    :param library: Существующая библиотека слов с кодами.
    :return: Словарь с новыми словами и их кодами, обновленная библиотека.
    """
    # Подсчитываем частоту слов
    frequency = {}
    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    # Отфильтровываем слова, которые уже есть в библиотеке
    new_words = {word: freq for word, freq in frequency.items() if word not in library}

    # Сортируем новые слова по частоте (по убыванию) и по длине (по убыванию)
    sorted_new_words = sorted(new_words.items(), key=lambda x: (-x[1], -len(x[0])))

    # Генерируем уникальные коды для новых слов
    new_codes = generate_codes(len(sorted_new_words))

    # Создаем словарь с новыми кодами
    new_word_dict = {}
    for i, (word, freq) in enumerate(sorted_new_words):
        new_word_dict[word] = new_codes[i]
        library[word] = new_codes[i]  # Добавляем в библиотеку

    return new_word_dict, library

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
    encrypted_tokens = [word_dict.get(token, token) for token in tokens]
    return ' '.join(encrypted_tokens)

def decrypt_text(encrypted_text, reverse_dict):
    """
    Расшифровывает текст, используя обратный словарь.

    :param encrypted_text: Зашифрованная строка.
    :param reverse_dict: Обратный словарь для декодирования.
    :return: Исходный текст.
    """
    tokens = encrypted_text.split()
    decrypted_tokens = [reverse_dict.get(token, token) for token in tokens]
    return ' '.join(decrypted_tokens)

def save_library(library, library_filename):
    """
    Сохраняет библиотеку слов в файл.

    :param library: Словарь с библиотекой слов.
    :param library_filename: Имя файла для сохранения библиотеки.
    """
    try:
        with open(library_filename, 'a', encoding='utf-8') as file:
            for word, code in library.items():
                file.write(f"{word}:{code}\n")
    except IOError as e:
        print(f"Ошибка при записи в файл библиотеки '{library_filename}': {e}")

def load_library(library_filename):
    """
    Загружает библиотеку слов из файла.

    :param library_filename: Имя файла библиотеки.
    :return: Словарь с библиотекой слов.
    """
    library = {}
    try:
        with open(library_filename, 'r', encoding='utf-8') as file:
            for line in file:
                if ':' in line:
                    word, code = line.strip().split(':', 1)
                    if word not in library and code not in library.values():
                        library[word] = code
    except FileNotFoundError:
        print(f"Файл библиотеки '{library_filename}' не найден. Создан новый файл.")
        with open(library_filename, 'w', encoding='utf-8') as file:
            pass
    except IOError as e:
        print(f"Ошибка при чтении файла библиотеки '{library_filename}': {e}")
    return library

def main():
    # Запрос режима работы
    print("Выберите режим работы:")
    print("1. Запаковать")
    print("2. Распаковать")
    choice = input("Введите 1 или 2: ").strip()

    if choice == '1':
        # Режим запаковки
        input_filename = input("Введите имя текстового файла: ")

        # Загрузка файла в строку
        file_line = load_file(input_filename, encoding='utf-8')  # Исправлено на 'utf-8'
        if not file_line:
            return

        # Очистка текста от недопустимых символов
        sanitized_text = sanitize_text(file_line)
        if file_line != sanitized_text:
            print("Обнаружены недопустимые символы. Они были заменены на '#'.")

        # Разбиение строки на слова и знаки препинания
        tokens = split_into_words(sanitized_text)

        # Загрузка существующей библиотеки
        library_filename = 'library.txt'
        library = load_library(library_filename)

        # Создание словаря новых слов и обновление библиотеки
        new_word_dict, library = create_word_dictionary(tokens, library)

        # Зашифровывание текста
        encrypted_text = encrypt_text(sanitized_text, new_word_dict)

        # Ввод имени выходного файла
        output_filename = input("Введите имя выходного файла (с расширением .dtc): ")

        # Сохранение зашифрованного текста в файл
        save_file(output_filename, encrypted_text, encoding='utf-8')

        # Сохранение обновленной библиотеки
        save_library(new_word_dict, library_filename)

    elif choice == '2':
        # Режим распаковки
        input_filename = input("Введите имя архивного файла (с расширением .dtc): ")

        # Загрузка файла в строку
        file_line = load_file(input_filename, encoding='utf-8')
        if not file_line:
            return

        # Загрузка существующей библиотеки
        library_filename = 'library.txt'
        library = load_library(library_filename)

        # Создание обратного словаря для декодирования
        reverse_dict = {code: word for word, code in library.items()}

        # Расшифровывание текста
        decrypted_text = decrypt_text(file_line, reverse_dict)

        # Ввод имени выходного файла
        output_filename = input("Введите имя выходного файла: ")

        # Сохранение расшифрованного текста в файл
        save_file(output_filename, decrypted_text, encoding='utf-8')

    else:
        print("Неверный выбор. Пожалуйста, выберите 1 для запаковки или 2 для распаковки.")

if __name__ == "__main__":
    main()
