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
- [Poetry](https://python-poetry.org/) (для управления зависимостями)

---

## Установка

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/Unker/msg_split.git
   cd msg_split
   ```

1. **Установите Poetry (если еще не установлен):**

   ```bash
   pip install poetry
   ```

1. **Установите зависимости:**

   - для использования
      ```bash
      poetry install --no-dev
      ```

   - для разработки
      ```bash
      poetry install
      ```
---

## Запуск тестов

Проект использует `pytest` для запуска тестов. Чтобы запустить все тесты, выполните:

```bash
poetry run pytest -v
```

### Запуск конкретного теста

Если вы хотите запустить конкретный тест, используйте команду, например:

```bash
poetry run pytest tests/test_split_message.py::TestSplitMessage::test_simple_html -v
```

### Покрытие кода тестами

Чтобы проверить покрытие кода тестами выполните:

```bash
poetry run pytest --cov=msg_split tests/
```

### Генерирование отчет о покрытии

Чтобы увидеть, какие строки не покрыты тестами, сгенерируйте отчет в формате HTML:

```bash
poetry run pytest --cov=msg_split --cov-report=html tests/
```
Далее перейдите в папку htmlcov и откройте index.html

---

## Использование

### Получение справки

```bash
poetry run python msg_split.py --help
```

### Пример использования

```bash
poetry run python msg_split.py --max-len=4396 ./tests/source.html
```

---


## Контакты

Если у вас есть вопросы или предложения, свяжитесь со мной:

- **Email:** kfil@yandex.ru
- **GitHub:** [Unker](https://github.com/Unker)