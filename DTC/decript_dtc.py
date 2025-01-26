import string
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

    sorted_words = sorted(frequency.items(), key=lambda x: (-x[1], -len(x[0])))

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

def decrypt_text(encrypted_text, reverse_dict):
    """
    Расшифровывает текст, используя обратный словарь.

    :param encrypted_text: Зашифрованная строка.
    :param reverse_dict: Обратный словарь для декодирования.
    :return: Исходный текст.
    """
    tokens = encrypted_text.split()
    decrypted_tokens = [reverse_dict.get(token, token) for token in tokens]
    return ''.join(decrypted_tokens)

def decrypt_file(input_filename, output_filename, library_filename):
    """
    Расшифровывает файл, используя библиотеку слов.

    :param input_filename: Имя входного файла.
    :param output_filename: Имя выходного файла.
    :param library_filename: Имя файла библиотеки.
    """
    library = load_library(library_filename)
    reverse_dict = {code: word for word, code in library.items()}
    text = load_file(input_filename)
    decrypted_text = decrypt_text(text, reverse_dict)
    save_file(output_filename, decrypted_text)

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
