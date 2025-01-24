import string  # Импорт модуля string
import re

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
    Очищает текст, удаляя специальные символы, пробелы, знаки переноса строки и цифры.
    Сохраняет только буквы (латинские и кириллические).

    :param text: Исходный текст.
    :return: Очищенный текст.
    """
    # Определяем допустимые символы: латинские и кириллические буквы
    allowed_chars = string.ascii_letters + "".join([chr(i) for i in range(ord('А'), ord('я')+1)])  # Добавлены кириллические символы

    # Заменяем недопустимые символы на пробел
    sanitized_text = ''.join([char if char in allowed_chars else ' ' for char in text])

    return sanitized_text

def create_word_dictionary(text):
    """
    Создает словарь слов с частотой.

    :param text: Текст для обработки.
    :return: Список отсортированных слов.
    """
    # Разделяем текст на слова
    words = text.split()

    # Подсчитываем частоту слов
    frequency = {}
    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    # Сортируем слова по частоте (по убыванию) и по длине (по убыванию)
    sorted_words = sorted(frequency.items(), key=lambda x: (-x[1], -len(x[0])))

    return sorted_words

def save_library(sorted_words, filename):
    """
    Сохраняет отсортированный список слов в файл, разделяя их символом переноса строки.

    :param sorted_words: Список отсортированных слов.
    :param filename: Имя файла для сохранения.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for word, freq in sorted_words:
                file.write(f"{word}\n")
    except IOError as e:
        print(f"Ошибка при записи в файл '{filename}': {e}")

def main():
    # Загрузка текста из файла
    text = load_file('source_lib.txt', encoding='utf-8')
    if not text:
        return

    # Очистка текста
    sanitized_text = sanitize_text(text)

    # Создание словаря слов
    sorted_words = create_word_dictionary(sanitized_text)

    # Сохранение библиотеки в файл
    save_library(sorted_words, 'word_lib.txt')

    print(f"Библиотека успешно создана и сохранена в 'word_lib.txt'.")

if __name__ == "__main__":
    main()
