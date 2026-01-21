# GraphRAG База Знаний

Веб-интерфейс на Streamlit для Microsoft GraphRAG с поддержкой DeepSeek API.

## Что такое GraphRAG?

GraphRAG — это система Retrieval-Augmented Generation (RAG) от Microsoft Research, которая использует **знаниевые графы** вместо простого векторного поиска. Это позволяет:

- Отвечать на **глобальные вопросы** ("Какие основные темы в документах?")
- Находить **скрытые связи** между сущностями
- Агрегировать информацию из **множества документов**

## Быстрая установка

### Одной командой

```bash
curl -sSL https://raw.githubusercontent.com/romannekrasovaillm/graphrag/claude/rag-system-analysis-12wV0/streamlit_app/install.sh | bash
```

### Вручную

```bash
git clone -b claude/rag-system-analysis-12wV0 https://github.com/romannekrasovaillm/graphrag.git
cd graphrag/streamlit_app
pip install -r requirements.txt
```

## Запуск

```bash
# Установить API ключи
export DEEPSEEK_API_KEY="sk-ваш-ключ-deepseek"
export JINA_API_KEY="jina_ваш-ключ-jina"

# Запустить
cd streamlit_app
streamlit run app.py
```

Открыть: http://localhost:8501

## Получение API ключей

| Провайдер | Ссылка | Примечание |
|-----------|--------|------------|
| DeepSeek | https://platform.deepseek.com/ | ~$0.14/1M токенов |
| Jina AI | https://jina.ai/ | 1M токенов бесплатно |

## Возможности интерфейса

### Вкладки в сайдбаре

| Вкладка | Описание |
|---------|----------|
| **Status** | Статус API ключей, статистика индекса |
| **Documents** | Загрузка документов (txt, csv, json, docx) |
| **Index** | Запуск индексации, настройка параметров |
| **Query** | Выбор метода поиска |

### Методы поиска

| Метод | Когда использовать | Пример вопроса |
|-------|-------------------|----------------|
| **Local** | Конкретные вопросы о сущностях | "Кто такой Иванов и с кем он работал?" |
| **Global** | Обзор, темы, суммаризация | "Какие основные направления исследований?" |
| **Drift** | Сложные многоэтапные вопросы | "Сравни подходы A и B в контексте задачи C" |
| **Basic** | Простой векторный поиск | Любые вопросы (baseline) |

## Использование

### 1. Загрузка документов

1. Перейдите на вкладку **Documents**
2. Перетащите файлы или нажмите **Browse files**
3. Нажмите **Add Documents**

Поддерживаемые форматы: `.txt`, `.csv`, `.json`, `.docx`

### 2. Индексация

1. Перейдите на вкладку **Index**
2. Выберите метод:
   - **Standard** — точнее, но дороже (LLM для всего)
   - **Fast** — быстрее и дешевле (NLP + LLM)
3. Настройте типы сущностей (для научных статей рекомендуется: person, organization, concept, method, dataset)
4. Нажмите **Run Indexing**

### 3. Задавайте вопросы

После завершения индексации чат станет активным. Введите вопрос и получите ответ с учётом всех ваших документов.

## Развёртывание на сервере

### Vast.ai / Облачная VM

```bash
# 1. Установить
git clone -b claude/rag-system-analysis-12wV0 https://github.com/romannekrasovaillm/graphrag.git ~/graphrag-kb
cd ~/graphrag-kb/streamlit_app
pip install -r requirements.txt

# 2. Установить ключи
export DEEPSEEK_API_KEY="sk-..."
export JINA_API_KEY="jina_..."

# 3. Запустить с туннелем (для внешнего доступа)
pip install cloudflared
nohup cloudflared tunnel --url http://localhost:8501 > tunnel.log 2>&1 &
sleep 5
cat tunnel.log | grep -o 'https://.*\.trycloudflare\.com'

# 4. Запустить приложение
streamlit run app.py --server.port=8501 --server.address=127.0.0.1
```

### Systemd сервис (автозапуск)

```bash
sudo tee /etc/systemd/system/graphrag.service << EOF
[Unit]
Description=GraphRAG Knowledge Base
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/graphrag-kb/streamlit_app
Environment="DEEPSEEK_API_KEY=sk-ваш-ключ"
Environment="JINA_API_KEY=jina_ваш-ключ"
ExecStart=/usr/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now graphrag
```

## Оценка стоимости

Для 500 научных статей (~5000 страниц):

| Компонент | Стоимость |
|-----------|-----------|
| DeepSeek (индексация) | ~$1-2 |
| Jina embeddings | Бесплатно (до 1M токенов) |
| **Итого** | **~$1-2** |

## Архитектура GraphRAG

```
Документы
    ↓
[Разбиение на чанки]
    ↓
[Извлечение сущностей и связей] ← LLM
    ↓
[Построение графа] ← NetworkX
    ↓
[Кластеризация] ← Leiden Algorithm
    ↓
[Генерация отчётов по сообществам] ← LLM
    ↓
[Создание эмбеддингов] ← Jina AI
    ↓
База знаний готова!
```

## Структура проекта

```
streamlit_app/
├── app.py                    # Главное приложение
├── components/
│   ├── chat.py              # Чат-интерфейс
│   └── sidebar.py           # Боковая панель настроек
├── services/
│   └── graphrag_service.py  # Обёртка над GraphRAG
├── requirements.txt
├── install.sh               # Скрипт установки
├── README.md                # Документация (EN)
└── README_RU.md             # Документация (RU)
```

## Решение проблем

### Индексация завершилась, но чат неактивен

Обновите страницу (F5) — статус индекса проверяется при загрузке.

### Ошибка "API key not found"

Убедитесь, что переменные окружения установлены **до** запуска:
```bash
echo $DEEPSEEK_API_KEY  # должен показать ключ
```

### Ошибка при загрузке .docx

Установите библиотеку:
```bash
pip install python-docx
```

### Не хватает памяти

- Используйте метод **Fast** вместо Standard
- Уменьшите размер чанков в настройках
- Добавьте swap: `sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

## Ссылки

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [DeepSeek API](https://platform.deepseek.com/)
- [Jina AI](https://jina.ai/)
- [Streamlit](https://streamlit.io/)

## Лицензия

MIT
