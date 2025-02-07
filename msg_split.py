from lxml import etree
from typing import Generator, List
import argparse

MAX_LEN = 4096
open_tags_stack: List[str] = []  # Стек для отслеживания открытых тегов
close_tags_stack: List[str] = []  # Стек для отслеживания закрытых тегов


def split_message(source: str, max_len=MAX_LEN) -> Generator[str, None, None]:
    """Splits the original message (`source`) into fragments of the specified length
    (`max_len`)."""

    def get_open_tag(element):
        """Формирует открывающий тег с атрибутами."""
        tag = f"<{element.tag}"
        for attr, value in element.attrib.items():
            tag += f' {attr}="{value}"'
        tag += ">"
        return tag

    def get_close_tag(element):
        """Формирует закрывающий тег."""
        return f"</{element.tag}>"

    def get_chunk(element, max_len, current_chunk=""):
        """Рекурсивно формирует фрагмент сообщения."""
        nonlocal open_tags_stack, close_tags_stack, is_full

        if element.tag == "body":
            if element.text:
                if len(current_chunk) + len(element.text) > max_len:
                    is_full = True
                    return element.text
                else:
                    current_chunk += element.text

            # Обходим дочерние элементы
            for child in element:
                current_chunk = get_chunk(child, max_len, current_chunk)
                if is_full:
                    break
        else:
            open_tag = get_open_tag(element)
            close_tag = get_close_tag(element)
            open_tags_stack.append(open_tag)
            close_tags_stack.append(close_tag)

            total_close_tags_length = sum(len(tag) for tag in close_tags_stack)

            # Пытаемся добавить весь блок
            html_text = etree.tostring(element, encoding="unicode", method="html")
            total_length = len(current_chunk) + len(html_text) + total_close_tags_length
            if total_length < max_len:
                current_chunk += html_text
                close_tags_stack.pop()
                open_tags_stack.pop()
                return current_chunk
            else:
                # Если нет потомков, то это должен быть последний блок в current_chunk
                if len(element) == 0:
                    # Отсекаем хвост
                    tail_length = max_len - total_length
                    tail_text = html_text[:tail_length]
                    current_chunk += tail_text
                    close_tags_stack.pop()
                    open_tags_stack.pop()
                    is_full = True
                    return current_chunk

            # Пытаемся добавить открывающий тег
            if len(current_chunk) + len(open_tag) + total_close_tags_length > max_len:
                close_tags_stack.pop()
                open_tags_stack.pop()
                is_full = True
                return current_chunk
            else:
                current_chunk += open_tag

            # Пытаемся добавить текст элемента
            if element.text:
                if (
                    len(current_chunk) + len(element.text) + total_close_tags_length
                    > max_len
                ):
                    is_full = True
                    return current_chunk
                else:
                    current_chunk += element.text

            # Обходим дочерние элементы
            for child in element:
                if is_full:
                    break
                current_chunk = get_chunk(child, max_len, current_chunk)

        return current_chunk

    open_tags_stack = []
    close_tags_stack = []
    is_full = False

    while True:
        if len(source) < max_len:
            yield source
            break

        # Парсим HTML
        tree = etree.fromstring(f"<body>{source}</body>")
        body_element = tree.xpath("//body")[0]

        chunk = get_chunk(body_element, max_len)
        chunk = chunk.replace("<body>", "").replace("</body>", "")

        # Удаляем обработанную часть из исходного элемента
        source = source.replace(chunk, "", 1)

        if not source:
            break

        # Закрываем все открытые теги
        close_tags = "".join(reversed(close_tags_stack))
        chunk += close_tags

        yield chunk

        is_full = False
        # Открываем тэги в новом фрагменте
        open_tags = "".join(open_tags_stack)
        open_tags_stack = []
        close_tags_stack = []
        source = open_tags + source


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split HTML message into fragments.")
    parser.add_argument(
        "--max-len", type=int, default=MAX_LEN, help="Maximum length of each fragment"
    )
    parser.add_argument("file", type=str, help="Path to the HTML file")

    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as file:
        source = file.read()

    try:
        for i, fragment in enumerate(split_message(source, args.max_len), 1):
            print(f"fragment #{i}: {len(fragment)} chars")
            print(fragment)
            print("-" * 40)
    except ValueError as e:
        print(f"Error: {e}")
