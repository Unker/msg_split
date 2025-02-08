import unittest
from unittest.mock import patch
from lxml import etree
from msg_split import _get_chunk, split_message


class TestSplitMessage(unittest.TestCase):
    def test_cannot_split_block(self):
        """Тест для случая, когда блок невозможно разбить."""
        html = "<div>This is a very long text that cannot be split</div>"
        max_len = 10  # Намеренно маленькое значение, чтобы вызвать ошибку

        with self.assertRaises(ValueError) as context:
            list(split_message(html, max_len))

        self.assertIn("Cannot split block", str(context.exception))

    def test_cannot_add_opening_tag(self):
        """Тест для случая, когда невозможно добавить открывающий тэг."""
        html = "<div><p>This is a very long text that cannot be split</p></div>"
        max_len = 10  # Намеренно маленькое значение, чтобы вызвать ошибку

        with self.assertRaises(ValueError) as context:
            list(split_message(html, max_len))

        self.assertIn("Cannot add opening tag", str(context.exception))

    def test_simple_html(self):
        """Тест для простого HTML-сообщения."""
        html = "<div><p>Hello</p><p>World</p></div>"
        max_len = 30
        fragments = list(split_message(html, max_len))

        # Проверяем количество фрагментов
        self.assertEqual(len(fragments), 2)

        # Проверяем содержимое фрагментов
        self.assertIn("<div><p>Hello</p></div>", fragments[0])
        self.assertIn("<div><p>World</p></div>", fragments[1])

    def test_infinity_loop(self):
        """Тест зацикливания."""
        html = "<div><p>Hello</p><p>World</p></div>"
        max_len = 25
        
        with self.assertRaises(ValueError) as context:
            list(split_message(html, max_len))

        self.assertIn("Potential infinite loop detected", str(context.exception))

    def test_no_split_needed(self):
        """Тест для сообщения, которое не требует разделения."""
        html = "<p>Hello World</p>"
        max_len = 100
        fragments = list(split_message(html, max_len))

        # Проверяем количество фрагментов
        self.assertEqual(len(fragments), 1)

        # Проверяем содержимое фрагмента
        self.assertEqual(fragments[0], html)

    def test_tags_closing(self):
        """Тест корректности закрытия тегов."""
        html = "<div><p>Hello</p><p>World</p></div>"
        max_len = 30
        fragments = list(split_message(html, max_len))

        # Проверяем, что все фрагменты имеют корректно закрытые теги
        for fragment in fragments:
            try:
                etree.fromstring(fragment)  # Парсим фрагмент
            except etree.XMLSyntaxError:
                self.fail(f"Фрагмент содержит некорректный HTML: {fragment}")

    def test_empty_input(self):
        """Тест для пустого входного сообщения."""
        html = ""
        max_len = 10
        fragments = list(split_message(html, max_len))

        # Проверяем, что результат пуст
        self.assertEqual(len(fragments), 1)

        # Проверяем содержимое фрагментов
        self.assertIn("", fragments[0])

    def test_complex_html(self):
        """Тест для сложного HTML с атрибутами."""
        html = '<div class="container">123<p id="p1">Hello</p><p id="p2">World</p></div>'
        max_len = 60
        fragments = list(split_message(html, max_len))

        # Проверяем количество фрагментов
        self.assertEqual(len(fragments), 2)

        # Проверяем содержимое фрагментов
        self.assertIn('<div class="container">123<p id="p1">Hello</p></div>', fragments[0])
        self.assertIn('<div class="container"><p id="p2">World</p></div>', fragments[1])
        
    def test_get_chunk(self):
        element = etree.fromstring('<div><p>Hello</p><p>World</p></div>')
        open_tags_stack = []
        close_tags_stack = []
        is_full = False

        result = _get_chunk(element, max_len=30, open_tags_stack=open_tags_stack, close_tags_stack=close_tags_stack, is_full=is_full)
        assert result == '<div><p>Hello</p>'

    def test_failed_to_remove_chunk(self):
        """Тест для случая, когда chunk не удаляется из source."""
        html = "<div><p>Hello</p><p>World</p></div>"
        max_len = 30

        # Мокаем функцию _get_chunk
        def mock_get_chunk(element, max_len, open_tags_stack, close_tags_stack, is_full, current_chunk=""):
            return "incorrect chunk html"

        with patch('msg_split._get_chunk', new=mock_get_chunk):
            with self.assertRaises(ValueError) as context:
                list(split_message(html, max_len))

            self.assertIn("Failed to remove chunk from source", str(context.exception))

    def test_failed_max_len(self):
        """chunk больше, чем max_len."""
        html = "<div><p>Hello</p><p>World</p></div>"
        max_len = 30

        # Мокаем функцию _get_chunk
        def mock_get_chunk(element, max_len, open_tags_stack, close_tags_stack, is_full, current_chunk=""):
            return "This chunk does not exist in the source"

        with patch('msg_split._get_chunk', new=mock_get_chunk):
            with self.assertRaises(ValueError) as context:
                list(split_message(html, max_len))

            self.assertIn("Chunk length exceeds max_len", str(context.exception))

    def test_multiple_disallowed_tags(self):
        """Тест для случая, когда в HTML несколько запрещенных тегов."""
        html = "<script><p>Hello</p><h1>World</h1><h2>Another</h2></script>"
        max_len = 35

        with self.assertRaises(ValueError) as context:
            list(split_message(html, max_len))

        # Проверяем, что сообщение об ошибке содержит информацию о первом запрещенном теге
        self.assertIn("Tag <script> is not allowed for splitting", str(context.exception))


if __name__ == "__main__":
    # unittest.main()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSplitMessage)
    runner = unittest.TextTestRunner(verbosity=2)  # Увеличиваем уровень детализации
    runner.run(suite)
