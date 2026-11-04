#!/usr/bin/env bash
# Перегенерує всі протоколи запусків у docs/evidence/ (виконувати з кореня репозиторію).
set -u
E=docs/evidence; mkdir -p $E
V10=models/history/rules_v1.0.json; V11=models/rules.json
python3 scripts/verify_quotes.py $V10 > $E/verify_quotes_v1.0.txt
python3 scripts/verify_quotes.py $V11 > $E/verify_quotes_v1.1.txt
python3 scripts/validate_rules.py $V11 > $E/validate_rules_v1.1.txt
python3 scripts/analyze_rules.py $V10 > $E/analysis_v1.0.txt
python3 scripts/analyze_rules.py $V11 > $E/analysis_v1.1.txt
python3 -m pytest -v --rules $V10 tests/test_gold.py > $E/pytest_gold_v1.0.txt 2>&1
python3 -m pytest -v --rules $V11 > $E/pytest_full_v1.1.txt 2>&1
python3 -m pytest -v --rules $V10 tests/test_traps.py > $E/pytest_traps_v1.0_after_engine_fix.txt 2>&1
python3 engine/engine.py > docs/explanations.txt
python3 -c "
from models.instances import SAMPLE_INSTANCES
for p,i in SAMPLE_INSTANCES: print(f'{type(i).__name__:12} {i.id:6} prefix={p:9} валідний; факти: {len(i.to_facts(p))}')
print(len(SAMPLE_INSTANCES), 'екземплярів пройшли валідацію')" > $E/frames_instances.txt
echo done
