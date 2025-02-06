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
  pass



def get_size(element):
    str = etree.tostring(element, encoding='unicode', method='html')
    str = str.replace("<body>", "").replace("</body>", "")
    sz = len(str)
    return sz

def get_chunk(element, max_len, chunk=None):
    
    if chunk is None:
      chunk = ''

    # Рекурсивно обходим всех дочерних элементов
    sz_element = get_size(element)
    print(f"tag {element.tag} sz={sz_element}")

    if element.tag != 'body':
      stack_cl.append(f"</{element.tag}>") 
      sz_close_tags = sum(len(s) for s in stack_cl)
    else:
      sz_close_tags = 0
    sz_total = len(chunk) + sz_element + sz_close_tags

    if sz_total < max_len:
      text_element = etree.tostring(element, encoding='unicode', method='html')
      stack_cl.pop()
      return text_element
    else:
      # пробуем разделить добавить дочерние элементы
      # проверяем есть ли потомки
      if len(element):
        # Добавляем открывающий тег текущего элемента
        open_tag = f"<{element.tag}>"
        text_element = open_tag
        # Добавляем текст текущего элемента
        if element.text:
          text_element += element.text
        
        chunk += text_element
        print(chunk)

        stack.append(element.tag)  # Добавляем тег в стек
        print(stack)
        for child in element:
          text_element = get_chunk(child, max_len, chunk)
          chunk += text_element
      else:
        # потомков нет. Закрываем чанк
        # stop iteration
        stack_cl.pop()  # контент тэга не поместится - убираем закрывающий тэг
        close_tags = ''.join(el for el in reversed(stack_cl))
        fixed_chunk = chunk + close_tags
        fixed_chunk = fixed_chunk.replace("<body>", "").replace("</body>", "")
        print(fixed_chunk)
        # тут нужно завершить все итерации и вернуть fixed_chunk в генератор
        return fixed_chunk


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Split HTML message into fragments.")
  parser.add_argument('--max-len', type=int, default=MAX_LEN, help="Maximum length of each fragment")
  parser.add_argument('file', type=str, help="Path to the HTML file")

  args = parser.parse_args()
  
  with open(args.file, 'r', encoding='utf-8') as file:
      source = file.read()

  tree = etree.HTML(source)
  body_content = tree.find('.//body')
  get_chunk(body_content, args.max_len)

  
#   try:
#       for i, fragment in enumerate(split_message(source, args.max_len), 1):
#           print(f"fragment #{i}: {len(fragment)} chars")
#           print(fragment)
#           print("-" * 40)
#   except ValueError as e:
#       print(f"Error: {e}")
