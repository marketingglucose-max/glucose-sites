# Сайты Glucose

- [Конкурентный анализ контента](https://marketingglucose-max.github.io/glucose-sites/glucose-competitor-analysis/) — Instagram ҰБТ-школ, неделя 02.11–08.11.2026
- [Ежедневный анализ конкурентов](https://marketingglucose-max.github.io/glucose-sites/daily/) — каждый день за прошедшие сутки

## Ежедневный анализ: как обновлять
1. Положить данные дня в `daily/data/ГГГГ-ММ-ДД.json` (формат — как у `2026-11-10.json`).
2. Запустить `python3 daily/build.py` — соберёт `daily/ГГГГ-ММ-ДД/index.html` и список дней `daily/index.html`.
3. Закоммитить и отправить в `main` — GitHub Pages опубликует сам.
