import string  # Импорт модуля string
import re
import os

def sanitize_text(chunk, allowed_chars):
    """
    Очищает текст, удаляя специальные символы, пробелы, знаки переноса строки и цифры.
    Сохраняет только буквы (латинские и кириллические).

    :param chunk: Часть текста для обработки.
    :param allowed_chars: Строка с допустимыми символами.
    :return: Очищенный текст.
    """
    # Используем генератор для обработки текста
    sanitized_chunk = ''.join(char if char in allowed_chars else ' ' for char in chunk)
    return sanitized_chunk

def process_file_in_chunks(file_path, chunk_size=1024*1024):
    """
    Читает файл по частям и обрабатывает каждую часть.

    :param file_path: Путь к файлу.
    :param chunk_size: Размер каждой части в байтах.
    :return: Генератор, возвращающий обработанные части текста.
    """
    allowed_chars = string.ascii_letters + "".join([chr(i) for i in range(ord('А'), ord('я')+1)])  # Добавлены кириллические символы
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            sanitized_chunk = sanitize_text(chunk, allowed_chars)
            yield sanitized_chunk

def count_words_in_chunks(chunks):
    """
    Подсчитывает частоту слов в обработанных частях текста.

    :param chunks: Генератор, возвращающий обработанные части текста.
    :return: Словарь с частотой слов.
    """
    frequency = {}
    for chunk in chunks:
        words = chunk.split()
        for word in words:
            frequency[word] = frequency.get(word, 0) + 1
    return frequency

def sort_words(frequency):
    """
    Сортирует слова по частоте и длине.

    :param frequency: Словарь с частотой слов.
    :return: Список отсортированных слов.
    """
    sorted_words = sorted(frequency.items(), key=lambda x: (-x[1], -len(x[0])))
    return sorted_words

def save_library(sorted_words, filename):
    """
    Сохраняет отсортированный список слов в файл.

    :param sorted_words: Список отсортированных слов.
    :param filename: Имя файла для сохранения.
    """
    with open(filename, 'w', encoding='utf-8') as file:
        for word, freq in sorted_words:
            file.write(f"{word}\n")

def main():
    # Путь к исходному файлу
    source_file = 'source_lib.txt'

    # Обработка файла по частям
    chunks = process_file_in_chunks(source_file)

    # Подсчет частоты слов
    frequency = count_words_in_chunks(chunks)

    # Сортировка слов
    sorted_words = sort_words(frequency)

    # Сохранение библиотеки в файл
    save_library(sorted_words, 'word_lib.txt')

    print(f"Библиотека успешно создана и сохранена в 'word_lib.txt'.")

if __name__ == "__main__":
    main()
