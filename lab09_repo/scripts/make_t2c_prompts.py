"""llm_log/prompts/t2c_v1.txt (шаблон) і llm_log/in/t2c_r{1,2}.txt (вхід для двох незалежних сліпих запусків; еталонів немає)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import t2c  # noqa: E402

TPL = """Ти пишеш запити Cypher (Neo4j 5) до графа знань (біомедичні дані: варіанти, гени, родичі). Нижче — схема графа.

{schema}

Завдання: для питання користувача напиши один запит Cypher лише для читання (MATCH/WHERE/WITH/RETURN). Поверни лише запит у блоці ```cypher.

Питання: {question}"""
ROOT = t2c.ROOT
(ROOT / "llm_log/prompts/t2c_v1.txt").write_text(TPL, encoding="utf-8")
qs = [json.loads(l) for l in (ROOT / "tests/t2c.jsonl").read_text(encoding="utf-8").splitlines()]
head = TPL.split("Питання: {question}")[0].replace("{schema}", t2c.schema_text())
for tier, suffix in (("easy", ""), ("hard", "h")):
    body = "\n".join(f"{q['id']}: {q['question']}" for q in qs if q["tier"] == tier)
    for r in (1, 2):
        (ROOT / f"llm_log/in/t2c_r{r}{suffix}.txt").write_text(head + "\n\nПитання (для КОЖНОГО окремо напиши запит; відповідай незалежно одне від одного):\n" + body + "\n", encoding="utf-8")
print(len(head))
