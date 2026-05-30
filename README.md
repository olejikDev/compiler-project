# Запуск лексера
python -m src.main lex --input examples/hello.src

# Подробный вывод с предупреждениями (--verbose не реализован, но можно так)
python -m src.main lex --input examples/hello.src

# Текстовый вывод AST (по умолчанию)
python -m src.main parse --input examples/hello.src --ast

# Сохранить AST в файл
python -m src.main parse --input examples/hello.src --ast > ast.txt

# JSON вывод для машинной обработки (через формат symbol table)
python -m src.main semantic --input examples/hello.src --dump-symbols --format json

# Подробный вывод с отладкой
python -m src.main check --input examples/hello.src --verbose

# Семантическая проверка программы
python -m src.main check --input examples/hello.src

# Вывод таблицы символов
python -m src.main semantic --input examples/hello.src --dump-symbols

# Вывод AST с типами
python -m src.main semantic --input examples/hello.src --dump-ast

# Генерация IR в текстовом формате
python -m src.main ir --input examples/arithmetic.src --format text

# Сохранить IR в файл
python -m src.main ir --input examples/factorial.src --output factorial.ir

# Статистика IR
python -m src.main ir --input examples/factorial.src --stats