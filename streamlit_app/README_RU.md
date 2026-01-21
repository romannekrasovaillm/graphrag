# GraphRAG База Знаний

Streamlit-интерфейс для Microsoft GraphRAG с DeepSeek API и локальными эмбеддингами Ollama.

## Что такое GraphRAG?

GraphRAG — это система Retrieval-Augmented Generation (RAG) от Microsoft Research, которая использует **знаниевые графы** вместо простого векторного поиска. Это позволяет:

- Отвечать на **глобальные вопросы** ("Какие основные темы в документах?")
- Находить **скрытые связи** между сущностями
- Агрегировать информацию из **множества документов**

## Быстрый старт

### 1. Установить Ollama (локальные эмбеддинги)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text
```

### 2. Клонировать и настроить

```bash
git clone -b claude/rag-system-analysis-12wV0 https://github.com/romannekrasovaillm/graphrag.git ~/graphrag-kb
cd ~/graphrag-kb/streamlit_app
pip install -r requirements.txt
```

### 3. Запустить

```bash
export DEEPSEEK_API_KEY="sk-ваш-ключ"
ollama serve &
streamlit run app.py --server.port=8501
```

Открыть: http://localhost:8501

## Одна команда для Vast.ai / VM

```bash
cd /workspace && ollama serve &>/dev/null & sleep 2 && export DEEPSEEK_API_KEY="sk-ваш-ключ" && pkill -f streamlit; pkill -f cloudflared; cd ~/graphrag-kb/streamlit_app && streamlit run app.py --server.port=8501 --server.address=0.0.0.0 &>/dev/null & sleep 3 && cloudflared tunnel --url http://localhost:8501
```

## Требования

| Компонент | Назначение | Стоимость |
|-----------|------------|-----------|
| DeepSeek API | LLM для извлечения и чата | ~$1-2 за 500 документов |
| Ollama | Локальные эмбеддинги | Бесплатно |

Получить DeepSeek API ключ: https://platform.deepseek.com/

## Возможности

- **Чат-интерфейс**: Задавайте вопросы по документам
- **4 метода поиска**: Local, Global, Drift, Basic
- **Загрузка документов**: Поддержка .txt, .csv, .json, .docx
- **Управление индексом**: Создание, обновление, очистка
- **Локальные эмбеддинги**: Ollama (nomic-embed-text) - бесплатно и быстро

## Методы поиска

| Метод | Когда использовать | Пример вопроса |
|-------|-------------------|----------------|
| **Local** | Конкретные вопросы о сущностях | "Кто такой Иванов и с кем он работал?" |
| **Global** | Обзор, темы, суммаризация | "Какие основные направления исследований?" |
| **Drift** | Сложные многоэтапные вопросы | "Сравни подходы A и B в контексте задачи C" |
| **Basic** | Простой векторный поиск | Любые вопросы (baseline) |

## Использование

### 1. Загрузка документов

1. Перейдите на вкладку **Documents** в сайдбаре
2. Перетащите файлы или нажмите **Browse files**
3. Нажмите **Add Documents**

### 2. Индексация

1. Перейдите на вкладку **Index**
2. Выберите метод:
   - **Standard** — точнее, но дороже
   - **Fast** — быстрее и дешевле (рекомендуется)
3. Нажмите **Run Indexing**

### 3. Задавайте вопросы

После индексации чат станет активным. Введите вопрос и получите ответ.

## Архитектура GraphRAG

```
Документы
    ↓
[Разбиение на чанки]
    ↓
[Извлечение сущностей и связей] ← DeepSeek LLM
    ↓
[Построение графа] ← NetworkX
    ↓
[Кластеризация] ← Leiden Algorithm
    ↓
[Генерация отчётов по сообществам] ← DeepSeek LLM
    ↓
[Создание эмбеддингов] ← Ollama (локально)
    ↓
База знаний готова!
```

## Структура проекта

```
streamlit_app/
├── app.py                    # Главное приложение
├── components/
│   ├── chat.py               # Чат-интерфейс
│   └── sidebar.py            # Боковая панель настроек
├── services/
│   └── graphrag_service.py   # Обёртка над GraphRAG
├── requirements.txt
└── README_RU.md
```

## Устранение неполадок

### Ollama не запущен

```bash
ollama serve &
ollama pull nomic-embed-text
```

### Индексация зависает

Проверьте, отвечает ли Ollama:
```bash
curl http://localhost:11434/v1/embeddings -d '{"model":"nomic-embed-text","input":"test"}' -H "Content-Type: application/json"
```

### Ошибка DeepSeek API

Проверьте API ключ:
```bash
curl https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Привет"}]}'
```

### Чат неактивен после индексации

Обновите страницу (F5).

### Не хватает памяти

- Используйте метод **Fast**
- Добавьте swap: `sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

## Ссылки

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [DeepSeek API](https://platform.deepseek.com/)
- [Ollama](https://ollama.com/)
- [Streamlit](https://streamlit.io/)

## Лицензия

MIT
