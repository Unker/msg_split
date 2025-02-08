#!/bin/bash

# Переход в директорию проекта (если скрипт запускается из другой директории)
cd "$(dirname "$0")" || exit

# Запуск скрипта через Poetry
poetry run python msg_split.py --max-len=4396 ./tests/source.html