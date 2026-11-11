# Самостійна робота 10 — Експеримент з embeddings

У папці збережено код, дані й результати; звіт DOCX/PDF не додається.

Склад і наявні результати
- Корпус: data/corpus.jsonl, 688 фрагментів.
- Золота розмітка: eval/gold_lab10.jsonl, 55 answerable запитів: 47 англійських і 8 українських.
- LLM-перефразування: eval/paraphrases.tsv.
- Зведені метрики: eval/results.json; по-запитні результати: eval/perq.json.
- Результати порівнюють MiniLM-L6, BGE-small, multilingual-e5-small, potion-8M та лексичний baseline BM25.

Фактичний recall@5 зі збереженого запуску:
  MiniLM-L6  0.7364
  BGE-small  0.7636
  mE5        0.7273
  potion-8M  0.4636
  BM25       0.7636

У src/build_sr10.py зафіксовано сім розбіжностей між моделями (Q03, Q06, Q09, Q13, Q29, Q44, Q35); це аналіз із даних, а не підтвердження причин для всіх помилок. Вибірка українських запитів мала (n=8). Перефразування виконані Claude Haiku; 4 із 55 перевірені перефрази мають легкий зсув змісту (Q10, Q20, Q24, Q31).

## Відтворення обчислень
1. Потрібні ваги для моделей, перелічених у src/emb.py, у каталогах models/minilm, models/bge, models/e5 і models/potion. Ваги до цієї папки не включені. У початковому середовищі використовували публічні ONNX-експорти з npm:
   `npm pack @ryanstark24/sfgraph-models@1.6.2 @coree-ai/coree-model-bge-small-en-v1.5@1.0.2 dsh-plugin-discover-model@0.1.0 counterparts-model-potion@0.1.0`
   Перевірте назви файлів у src/emb.py та README npm-пакетів; ці пакети не є частиною репозиторію.
2. Встановіть залежності для експерименту: numpy, onnxruntime, tokenizers, rank-bm25.
3. Із цієї папки (`10_SR`) запустіть `python -X utf8 src/exp.py` (Windows) або `python src/exp.py` (Linux). Скрипт перезапише `eval/results.json` та `eval/perq.json`.

Не запускайте src/build_sr10.py, якщо потрібні лише код і дані: ця допоміжна програма створює оформлені файли, зокрема DOCX. Метрики вже збережені в eval/; новий прогін без ваг виконати неможливо.
