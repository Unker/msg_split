from lxml import etree
from typing import Generator, List
import click

MAX_LEN: int = 4096
open_tags_stack: List[str] = []  # Стек для отслеживания открытых тегов
close_tags_stack: List[str] = []  # Стек для отслеживания закрытых тегов

def split_message(source: str, max_len: int = MAX_LEN) -> Generator[str, None, None]:
    """Splits the original message (`source`) into fragments of the specified length
    (`max_len`)."""

    def get_open_tag(element: etree._Element) -> str:
        """Формирует открывающий тег с атрибутами."""
        tag: str = f"<{element.tag}"
        for attr, value in element.attrib.items():
            tag += f' {attr}="{value}"'
        tag += ">"
        return tag

    def get_close_tag(element: etree._Element) -> str:
        """Формирует закрывающий тег."""
        return f"</{element.tag}>"

    def get_chunk(
        element: etree._Element, max_len: int, current_chunk: str = ""
    ) -> str:
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
                if is_full:
                    break
                current_chunk = get_chunk(child, max_len, current_chunk)
        else:
            open_tag: str = get_open_tag(element)
            close_tag: str = get_close_tag(element)
            open_tags_stack.append(open_tag)
            close_tags_stack.append(close_tag)

            total_close_tags_length: int = sum(len(tag) for tag in close_tags_stack)

            # 1. Пытаемся добавить весь блок
            html_text: str = etree.tostring(element, encoding="unicode", method="html")
            total_length: int = len(current_chunk) + len(html_text) + total_close_tags_length
            if total_length < max_len:
                current_chunk += html_text
                close_tags_stack.pop()
                open_tags_stack.pop()
                return current_chunk
            else:
                # Если нет потомков
                if len(element) == 0:
                    if current_chunk != "":
                        # Возвращаем что получилось накопить. Возможно этот блок поместится в следующей итерации
                        close_tags_stack.pop()
                        open_tags_stack.pop()
                        is_full = True
                        return current_chunk
                    else:
                        raise ValueError(
                            f"Cannot split block: {get_open_tag(element)} (text too long)"
                        )

            # 2. Пытаемся добавить открывающий тег
            if len(current_chunk) + len(open_tag) + total_close_tags_length > max_len:
                close_tags_stack.pop()
                open_tags_stack.pop()
                is_full = True
                if current_chunk == "":
                    raise ValueError(
                        f"Cannot add opening tag: {get_open_tag(element)} (not enough space)"
                    )
                else:
                    return current_chunk
            else:
                current_chunk += open_tag

            # 3. Пытаемся добавить текст элемента
            if element.text:
                if (
                    len(current_chunk) + len(element.text) + total_close_tags_length
                    > max_len
                ):
                    raise ValueError(
                        f"Cannot add text from: {get_open_tag(element)} (not enough space)"
                    )
                else:
                    current_chunk += element.text

            # 4. Обходим дочерние элементы
            for child in element:
                if is_full:
                    break
                current_chunk = get_chunk(child, max_len, current_chunk)

        return current_chunk

    open_tags_stack = []
    close_tags_stack = []
    is_full: bool = False
    previous_source_length: int = len(source)  # Для проверки на зацикливание

    while True:
        if len(source) < max_len:
            yield source
            break

        # Парсим HTML
        tree: etree._ElementTree = etree.fromstring(f"<body>{source}</body>")
        body_element: etree._Element = tree.xpath("//body")[0]

        try:
            chunk: str = get_chunk(body_element, max_len)
            chunk = chunk.replace("<body>", "").replace("</body>", "")
            if len(chunk) > max_len:
                raise ValueError(f"Chunk length exceeds max_len: {len(chunk)} > {max_len}")

            # Удаляем обработанную часть из исходного элемента
            source_before_length: int = len(source)
            source = source.replace(chunk, "", 1)
            source_after_length: int = len(source)
            if source_before_length - source_after_length == 0:
                raise ValueError(
                    f"Failed to remove chunk from source: {source[:len(chunk)]}. Chunk: '{chunk}'"
                )

            if not source:
                break

            # Закрываем все открытые теги
            close_tags: str = "".join(reversed(close_tags_stack))
            chunk += close_tags

            yield chunk

            is_full = False
            # Открываем тэги в новом фрагменте
            open_tags: str = "".join(open_tags_stack)
            open_tags_stack = []
            close_tags_stack = []

            # Проверка на зацикливание
            new_source: str = open_tags + source
            if len(new_source) >= previous_source_length:
                raise ValueError("Potential infinite loop detected: source length did not decrease")
            previous_source_length = len(new_source)

            source = new_source

        except ValueError as e:
            raise e

@click.command()
@click.option(
    "--max-len",
    type=int,
    default=MAX_LEN,
    help="Maximum length of each fragment.",
    show_default=True,
)
@click.argument("file", type=click.Path(exists=True, readable=True))
def main(max_len: int, file: str) -> None:
    """Split HTML message into fragments.
    """
    with open(file, "r", encoding="utf-8") as f:
        source: str = f.read()

    try:
        for i, fragment in enumerate(split_message(source, max_len), 1):
            click.echo(f"fragment #{i}: {len(fragment)} chars")
            click.echo(fragment)
            click.echo("-" * 40)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    main()
