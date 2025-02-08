# msg_split

Скрипт для разделения HTML-сообщения на фрагменты заданной длины.

## Оглавление

1. [Требования](#требования)
2. [Установка](#установка)
3. [Запуск тестов](#запуск-тестов)
4. [Использование](#использование)
5. [Контакты](#контакты)

---

## Требования

Для работы понадобится:

- Python 3.8 или выше

---

## Установка

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/Unker/msg_split.git
   cd вmsg_split
   ```

1. **Создайте виртуальное окружение:**

   ```bash
   python -m venv .venv
   ```

1. **Активируйте виртуальное окружение:**

   - На Windows:

     ```bash
     .venv/bin/activate
     ```

   - На macOS/Linux:

     ```bash
     source .venv/bin/activate
     ```

1. **Установите зависимости:**

   - для использования
      ```bash
      pip install -r requirements.txt
      ```

   - для разработки
      ```bash
      pip install -r requirements-dev.txt
      ```
---

## Запуск тестов

Проект использует `pytest` для запуска тестов. Чтобы запустить все тесты, выполните:

```bash
pytest -v
```

### Запуск конкретного теста

Если вы хотите запустить конкретный тест, используйте команду, например:

```bash
pytest tests/test_split_message.py::TestSplitMessage::test_simple_html -v
```

### Покрытие кода тестами

Чтобы проверить покрытие кода тестами выполните:

```bash
pytest --cov=msg_split tests/
```

---

## Использование

### Пример использования

```bash
python msg_split.py --max-len=4396 ./tests/source.html 
```

---


## Контакты

Если у вас есть вопросы или предложения, свяжитесь со мной:

- **Email:** kfil@yandex.ru
- **GitHub:** [Unker](https://github.com/Unker)