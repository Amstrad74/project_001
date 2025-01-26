import sys
import importlib

# Динамический импорт модулей
try:
    encript_dtc = importlib.import_module('encript_dtc')
    decript_dtc = importlib.import_module('decript_dtc')
except ImportError as e:
    print(f"Ошибка при импорте модулей: {e}")
    sys.exit(1)

def main():
    # Запрос режима работы
    print("Выберите режим работы:")
    print("1. Запаковать")
    print("2. Расшифровать")
    choice = input("Введите 1 или 2: ").strip()

    if choice == '1':
        # Режим запаковки
        input_filename = input("Введите имя текстового файла: ")

        # Загрузка файла в строку
        file_line = encript_dtc.load_file(input_filename, encoding='utf-8')
        if not file_line:
            return
        print(file_line)
        # Очистка текста
        sanitized_text = encript_dtc.sanitize_text(file_line)

        # Разбиение текста на токены
        tokens = enict_dtc.split_into_words(sanitized_text)

        # Загрузка существующей библиотеки
        library_filename = 'library.json'
        library = encript_dtc.load_library(library_filename)

        # Создание словаря новых слов и обновление библиотеки
        new_word_dict, reverse_dict = encript_dtc.create_word_dictionary(tokens)

        # Зашифровывание текста
        encrypted_text = encript_dtc.encrypt_text(sanitized_text, new_word_dict)

        # Ввод имени выходного файла
        output_filename = input("Введите имя выходного файла (с расширением .dtc): ")

        # Сохранение зашифрованного текста в файл
        encript_dtc.save_file(output_filename, encrypted_text, encoding='utf-8')

        # Сохранение обновленной библиотеки
        encript_dtc.save_library(new_word_dict, library_filename)

    elif choice == '2':
        # Режим расшифровки
        input_filename = input("Введите имя архивного файла (с расширением .dtc): ")

        # Загрузка файла в строку
        file_line = encript_dtc.load_file(input_filename, encoding='utf-8')  # Исправлено на 'encript_dtc.load_file'
        if not file_line:
            return

        # Загрузка существующей библиотеки
        library_filename = 'library.json'
        library = decript_dtc.load_library(library_filename)

        # Создание обратного словаря для декодирования
        reverse_dict = {code: word for word, code in library.items()}

        # Расшифровывание текста
        decrypted_text = decript_dtc.decrypt_text(file_line, reverse_dict)

        # Ввод имени выходного файла
        output_filename = input("Введите имя выходного файла: ")

        # Сохранение расшифрованного текста в файл
        encript_dtc.save_file(output_filename, decrypted_text, encoding='utf-8')  # Исправлено на 'encript_dtc.save_file'

    else:
        print("Неверный выбор. Пожалуйста, выберите 1 для запаковки или 2 для расшифровки.")

if __name__ == "__main__":
    main()
'''
Пояснения:

    1.
    Функция read_txt_files_from_folder:
        Читает все файлы .txt из указанной папки и объединяет их содержимое в одну строку.
        Функция проверяет каждый файл на соответствие расширению .txt и добавляет его содержимое к общей строке.
    2.
    Обновленная функция main:
        Сначала читает все файлы из папки txt и объединяет их в файл source_lib.txt.
        Затем продолжает работу как и раньше: загружает текст из source_lib.txt, очищает его и создает 
        словарь-библиотеку.
    3.
    Использование модуля os:
        Модуль os используется для работы с файловой системой, чтобы найти все файлы .txt в папке txt.
    4.
    Проверка кодировки и переконвертация:
        Функция load_file уже обрабатывает ошибки декодирования и пытается переконвертировать файлы из 
        кодировки cp1251 в utf-8, если это необходимо.

Запуск программы:

    1.Убедитесь, что папка txt находится в той же директории, что и программа create_lib.py.
    2.
    Запустите программу с помощью команды:

    bash

    python create_lib.py

    3.Программа прочитает все файлы .txt из папки txt, объединит их в файл source_lib.txt, а затем создаст 
    словарь-библиотеку и сохранит его в файл word_lib.txt.

Теперь программа автоматически обрабатывает все текстовые файлы в папке txt, проверяет их кодировку и объединяет 
их в один файл перед созданием словаря-библиотеки.

'''