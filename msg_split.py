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
  # Инициализация стека для закрывающих тегов
  stack = []
  stack_cl = []
  is_full = False

  # Рекурсивная функция для получения фрагмента
  def get_chunk(element, max_len, chunk=""):
      nonlocal stack, stack_cl, is_full

      sz_close_tags = sum(len(s) for s in stack_cl) # размер закрывающих тэгов
      if element.tag != 'body':
        html_text = etree.tostring(element, encoding='unicode', method='html')

        # Формируем открывающий тег с атрибутами
        open_tag = f"<{element.tag}"
        for attr, value in element.attrib.items():
          open_tag += f' {attr}="{value}"'
        open_tag += ">"
        stack.append(open_tag)  # Добавляем открытый тег 
        stack_cl.append(f"</{element.tag}>")  # Добавляем закрывающий тег в стек

        # 1. Пытаемся добавить весь блок
        sz_total = len(chunk) + len(html_text) + sz_close_tags
        if sz_total < max_len:
          chunk += html_text
          stack_cl.pop()
          stack.pop()
          return chunk

        # 2. Пытаемся добавить тэг
        if len(chunk) + len(open_tag) + sz_close_tags > max_len:
          stack_cl.pop()
          stack.pop()
          is_full = True
          return chunk
        else:
          chunk += open_tag

      # 3. Пытаемся добавть контент текущего блока
      if element.text:
        if len(chunk) + len(element.text) + sz_close_tags > max_len:
          is_full = True
          return chunk
        else:
            chunk += element.text

      # 4. Обходим дочерние элементы
      for child in element:
        if is_full:
          break
        text_child = etree.tostring(child, encoding='unicode', method='html')

        # Формируем открывающий тег с атрибутами
        open_tag = f"<{child.tag}"
        for attr, value in child.attrib.items():
          open_tag += f' {attr}="{value}"'
        open_tag += ">"
        stack.append(open_tag)  # Добавляем открытый тег 
        stack_cl.append(f"</{child.tag}>")  # Добавляем закрывающий тег в стек

        sz_close_tags = sum(len(s) for s in stack_cl) # размер закрывающих тэгов
        sz_total = len(chunk) + len(text_child) + sz_close_tags

        if sz_total >= max_len:
          # пытаемся разбить блоки потомка
          if len(child): # test if it has children
            # добавим тэг и контент текущего блока
            if len(chunk) + len(open_tag) + sz_close_tags > max_len:
              # не помещается контент блока
              # TODO определиться что делать
              is_full = True
              return chunk
            else:
              chunk += open_tag

            if child.text:
              if len(chunk) + len(child.text) + sz_close_tags > max_len:
                is_full = True
                return chunk
              else:
                  chunk += child.text

            for children in child:
              chunk = get_chunk(children, max_len, chunk)
              if is_full:
                break
          else:
            # нет потомков
            # return chunk
            stack_cl.pop()
            stack.pop()
            is_full = True
            break
        else:
          chunk += text_child
          stack_cl.pop()
          stack.pop()

      return chunk

  # Генератор фрагментов
  while True:
      if len(source) < max_len:
        yield source
        break

      # Парсим HTML
      tree = etree.fromstring(f"<body>{source}</body>")
      text_element = etree.tostring(tree, encoding='unicode', method='html')
      body_element = tree.xpath("//body")[0]

      chunk = get_chunk(body_element, max_len)

      # Удаляем обработанную часть из исходного элемента
      source = source.replace(chunk, "", 1)

      if not source:
          break
      
      # Закрываем все открытые теги
      close_tags = "".join(reversed(stack_cl))
      chunk += close_tags
      chunk = chunk.replace("<body>", "").replace("</body>", "")

      yield chunk

      is_full = False
      # открываем тэги в новом фрагменте
      open_tags = "".join((stack))
      stack = []
      stack_cl = []
      source = open_tags + source



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
      # пробуем разделить дочерние элементы
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
          new_chunk = get_chunk(child, max_len, chunk)
          if new_chunk == 'end iteration':
              break
          chunk += new_chunk
      else:
        # потомков нет. Закрываем чанк
        # stop iteration
        stack_cl.pop()  # контент тэга не поместится - убираем закрывающий тэг
        close_tags = ''.join(el for el in reversed(stack_cl))
        fixed_chunk = chunk + close_tags
        fixed_chunk = fixed_chunk.replace("<body>", "").replace("</body>", "")
        print(fixed_chunk)
        # тут нужно завершить все итерации и вернуть fixed_chunk в генератор
        chunk = fixed_chunk
        return 'end iteration'


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Split HTML message into fragments.")
  parser.add_argument('--max-len', type=int, default=MAX_LEN, help="Maximum length of each fragment")
  parser.add_argument('file', type=str, help="Path to the HTML file")

  args = parser.parse_args()
  
  with open(args.file, 'r', encoding='utf-8') as file:
      source = file.read()

  tree = etree.HTML(source)
  body_content = tree.find('.//body')
  # get_chunk(body_content, args.max_len)

  for fragment in split_message(source, max_len=200):
    print("Фрагмент:")
    print(fragment)
    print("-" * 40)

  
#   try:
#       for i, fragment in enumerate(split_message(source, args.max_len), 1):
#           print(f"fragment #{i}: {len(fragment)} chars")
#           print(fragment)
#           print("-" * 40)
#   except ValueError as e:
#       print(f"Error: {e}")
