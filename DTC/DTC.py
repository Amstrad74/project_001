import string
import re
import struct
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
                    return file.read()
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
    return ''.join([char if char in allowed_chars else ' ' for char in text])

def split_into_words(text):
    """
    Разделяет текст на слова и разделительные символы.

    :param text: Исходный текст.
    :return: Список слов и разделительных символов.
    """
    pattern = r'(\w+|[^\w\s]+|\s+)'
    return re.findall(pattern, text)

def load_binary_library(library_filename):
    """
    Загружает библиотеку слов из бинарного файла.

    :param library_filename: Имя файла библиотеки.
    :return: Словарь с библиотекой слов.
    """
    library = {}
    try:
        with open(library_filename, 'rb') as file:
            while True:
                word_length = struct.unpack('I', file.read(4))[0]
                if word_length == 0:
                    break
                word = file.read(word_length).decode('utf-8')
                code_length = struct.unpack('B', file.read(1))[0]
                code = file.read(code_length).hex()
                library[word] = code
    except FileNotFoundError:
        print(f"Файл библиотеки '{library_filename}' не найден.")
    except IOError as e:
        print(f"Ошибка при чтении файла библиотеки '{library_filename}': {e}")
    return library

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
        byte_length = (current.bit_length() + 7) // 8
        byte_list = current.to_bytes(byte_length, byteorder='big')
        # Проверяем, что все байты не запрещены
        if all(not is_forbidden_code(b) for b in byte_list):
            hex_str = byte_list.hex()
            codes.append(hex_str)
            if len(codes) == count:
                break

        # Увеличиваем текущий код на 1
        current += 1
        if current.bit_length() > 32:
            raise ValueError("Количество кодов слишком велико для генерации.")

    return codes

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
                file.write(struct.pack('B', len(code) // 2))  # Делим на 2, так как hex_str - это строка из двух символов на байт
                # Записываем код
                file.write(bytes.fromhex(code))
    except IOError as e:
        print(f"Ошибка при записи в файл '{filename}': {e}")

def process_files_in_folder(folder_path, output_folder, library_filename):
    """
    Обрабатывает все файлы в указанной папке, шифруя их.

    :param folder_path: Путь к папке с исходными файлами.
    :param output_folder: Путь к папке для сохранения зашифрованных файлов.
    :param library_filename: Имя файла библиотеки.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            input_path = os.path.join(folder_path, filename)
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.dtc"
            output_path = os.path.join(output_folder, output_filename)
            dynamic_library_filename = f"{base_name}.dtl"
            dynamic_library_path = os.path.join(output_folder, dynamic_library_filename)
            encrypt_file(input_path, output_path, dynamic_library_path)

def encrypt_file(input_filename, output_filename, library_filename):
    """
    Шифрует файл, используя библиотеку слов.

    :param input_filename: Имя входного файла.
    :param output_filename: Имя выходного файла.
    :param library_filename: Имя файла библиотеки.
    """
    library = load_binary_library(library_filename)
    text = load_file(input_filename)
    encrypted_text = encrypt_text(text, library)
    save_file(output_filename, encrypted_text)

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

def decrypt_file(input_filename, output_filename, library_filename):
    """
    Расшифровывает файл, используя библиотеку слов.

    :param input_filename: Имя входного зашифрованного файла.
    :param output_filename: Имя выходного файла для сохранения расшифрованного текста.
    :param library_filename: Имя файла библиотеки.
    """
    library = load_binary_library(library_filename)
    reverse_dict = {code: word for word, code in library.items()}
    text = load_file(input_filename)
    decrypted_text = decrypt_text(text, reverse_dict)
    save_file(output_filename, decrypted_text)

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

    # Путь к файлу статической библиотеки
    static_library_filename = 'word_lib.dtl'

    # Загружаем статическую библиотеку
    static_library = load_binary_library(static_library_filename)

    # Если статическая библиотека не существует, создаем динамическую библиотеку
    if not static_library:
        dynamic_library = {}
        last_number = 0
    else:
        # Определяем последний номер в статической библиотеке
        last_number = max([int(code, 16) for code in static_library.keys()])
        dynamic_library = {}

    # Создание динамической библиотеки
    if not os.path.exists(static_library_filename):
        # Если статическая библиотека не существует, начинаем с 1
        dynamic_start = 1
        dynamic_codes = generate_hex_codes(1000)  # Генерируем 1000 кодов
        for code in dynamic_codes:
            dynamic_library[code] = ""
    else:
        # Если статическая библиотека существует, начинаем с последнего номера + 1
        dynamic_start = last_number + 1
        dynamic_codes = generate_hex_codes(1000)  # Генерируем 1000 кодов
        for code in dynamic_codes:
            dynamic_library[code] = ""

    # Проверка на совпадение версий
    if static_library and dynamic_library:
        # Получаем последний номер статической библиотеки
        last_static_number = max([int(code, 16) for code in static_library.keys()])
        # Получаем первый номер динамической библиотеки
        first_dynamic_number = min([int(code, 16) for code in dynamic_library.keys()])
        if first_dynamic_number != last_static_number + 1:
            print(f"Нужна word_lib с количеством слов в словаре, равным {first_dynamic_number - 1}.")
            return
    elif static_library:
        # Если динамическая библиотека не существует, используем только статическую
        dynamic_library = {}
    elif dynamic_library:
        # Если статическая библиотека не существует, используем только динамическую
        static_library = {}

    # Объединение статической и динамической библиотек
    combined_library = {**static_library, **dynamic_library}

    # Шифрование файлов
    process_files_in_folder(txt_folder, dtc_folder, library_filename=static_library_filename)

    # Сохранение динамической библиотеки
    if dynamic_library:
        dynamic_library_path = os.path.join(dtc_folder, 'dynamic_library.dtl')
        save_binary_library(list(dynamic_library.keys()), list(dynamic_library.values()), dynamic_library_path)

    print("Процесс шифрования завершен.")

    # Дешифрование файлов
    process_files_in_folder(dtc_folder, decript_folder, library_filename=static_library_filename)

    # Проверка совпадения оригинальных и расшифрованных файлов
    if verify_files(txt_folder, decript_folder):
        print("Все файлы совпадают с оригиналами.")
    else:
        print("Ошибка: файлы не совпадают.")

if __name__ == "__main__":
    main()
