# Рабочий пример: неделя 20–26 июля 2026, команда Анара

Файлы этой папки — полный вход конвейера. Отчёт, собранный из них, лежит в `reports/2026-07-20_2026-07-26/`.

| Файл | Что это |
|---|---|
| `config.json` | команда, период, префикс ссылок amoCRM, названия колонок выгрузки метрик, пороги |
| `metrics.json` | выгрузка метрик по менеджерам, строка «Всего» — итог группы |
| `content.json` | всё, что написала модель: выводы недели, паттерны, разборы, планы развития, лучшие практики |
| `data.json` | результат первого шага конвейера: числа, метки, признаки этапов, профили менеджеров |

Повторить прогон из корня репозитория:

```bash
SKILL=skills/eduson-weekly-quality-report
WORK=/tmp/okk && mkdir -p $WORK && cp $SKILL/example/{config.json,metrics.json,content.json} $WORK/

python3 $SKILL/pipeline/build_data.py \
  --calls calls/2026-07-20_2026-07-26/prompt_custom_query_20260729_0217.txt \
  --metrics $WORK/metrics.json --config $WORK/config.json --content $WORK/content.json --out $WORK/data.json

python3 $SKILL/pipeline/render_report.py --data $WORK/data.json --content $WORK/content.json --outdir $WORK/out
python3 $SKILL/pipeline/render_html.py --md $WORK/out/REPORT.md --logo eduson-design-book/eduson-logo.png --out $WORK/out/index.html
python3 $SKILL/pipeline/verify.py --outdir $WORK/out --data $WORK/data.json --content $WORK/content.json

diff -q $WORK/out/REPORT.md reports/2026-07-20_2026-07-26/REPORT.md
diff -q $WORK/out/index.html reports/2026-07-20_2026-07-26/index.html
```

Оба сравнения обязаны молчать: конвейер воспроизводит опубликованный отчёт побайтно.

Ориентиры прогона: 279 клиентов, 98 разобранных сделок, 109 разговоров, 7 менеджеров, балл группы 71,0, 7 системных паттернов, 3 разбора «ниже среднего», категории A21 · B50 · C26.
