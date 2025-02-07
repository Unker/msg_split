from lxml import etree
from lxml import html
from typing import Generator, List
import argparse

MAX_LEN = 4096
stack: List[str] = []  # Стек для отслеживания открытых тегов
stack_cl: List[str] = []  # Стек для отслеживания закрытых тегов

def split_message(source: str, max_len=MAX_LEN) -> Generator[str, None, None]:
  """Splits the original message (`source`) into fragments of the specified length
  (`max_len`)."""
  def get_open_tag(element):
      """Формирует открывающий тег с атрибутами."""
      open_tag = f"<{element.tag}"
      for attr, value in element.attrib.items():
          open_tag += f' {attr}="{value}"'
      open_tag += ">"
      return open_tag

  def get_close_tag(element):
      """Формирует закрывающий тег."""
      return f"</{element.tag}>"

  def get_chunk(element, max_len, chunk=""):
      """Рекурсивно формирует фрагмент сообщения."""
      nonlocal stack, stack_cl, is_full

      if element.tag == 'body':
        if element.text:
          if len(chunk) + len(element.text) > max_len:
            is_full = True
            return element.text
          else:
            chunk += element.text

        # Обходим дочерние элементы
        for child in element:
          chunk = get_chunk(child, max_len, chunk)
          if is_full:
            break
        
      else:
        open_tag = get_open_tag(element)
        close_tag = get_close_tag(element)
        stack.append(open_tag)
        stack_cl.append(close_tag)

        sz_close_tags = sum(len(s) for s in stack_cl)

        # Пытаемся добавить весь блок
        html_text = etree.tostring(element, encoding='unicode', method='html')
        sz_total = len(chunk) + len(html_text) + sz_close_tags
        if sz_total < max_len:
            chunk += html_text
            stack_cl.pop()
            stack.pop()
            return chunk
        else:
          # Если нет потомком, то это должен быть последний блок в chunk
          if len(element) == 0:
            # отсекаем хвост
            tail = max_len-sz_total
            tail_text = html_text[:tail]
            chunk += tail_text
            stack_cl.pop()
            stack.pop()
            is_full = True
            return chunk

        # Пытаемся добавить открывающий тег
        if len(chunk) + len(open_tag) + sz_close_tags > max_len:
            stack_cl.pop()
            stack.pop()
            is_full = True
            return chunk
        else:
            chunk += open_tag

        # Пытаемся добавить текст элемента
        if element.text:
            if len(chunk) + len(element.text) + sz_close_tags > max_len:
                is_full = True
                return chunk
            else:
                chunk += element.text

        # Обходим дочерние элементы
        for child in element:
            if is_full:
                break
            chunk = get_chunk(child, max_len, chunk)

      # if not is_full:
      #     chunk += close_tag
      #     stack_cl.pop()
      #     stack.pop()

      return chunk

  stack = []
  stack_cl = []
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
      close_tags = "".join(reversed(stack_cl))
      chunk += close_tags

      yield chunk

      is_full = False
      # Открываем тэги в новом фрагменте
      open_tags = "".join(stack)
      stack = []
      stack_cl = []
      source = open_tags + source





if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Split HTML message into fragments.")
  parser.add_argument('--max-len', type=int, default=MAX_LEN, help="Maximum length of each fragment")
  parser.add_argument('file', type=str, help="Path to the HTML file")

  args = parser.parse_args()
  
  with open(args.file, 'r', encoding='utf-8') as file:
      source = file.read()

  # tree = etree.HTML(source)
  # body_content = tree.find('.//body')

  # for fragment in split_message(source, max_len=200):
  #   print("Фрагмент:")
  #   print(fragment)
  #   print("-" * 40)

  
  try:
      for i, fragment in enumerate(split_message(source, args.max_len), 1):
          print(f"fragment #{i}: {len(fragment)} chars")
          print(fragment)
          print("-" * 40)
  except ValueError as e:
      print(f"Error: {e}")
