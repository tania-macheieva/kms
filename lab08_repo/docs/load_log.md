# Журнал завантаження

- Дата й час завантаження: **2026-11-04 17:19:50** (Europe/Kiev)
- Триплстор: **pyoxigraph 0.5.13** (вбудований SPARQL 1.1 стор на RocksDB, каталог `store/`) — замість Apache Jena Fuseki/GraphDB (Docker і завантаження JAR тут недоступні)
- Версія графа знань: **kb-0.1.0** (контрольні суми файлів нижче)
- Dataset: іменовані графи `urn:dkh:graph:{tbox,abox,inferred,links}`; запити виконуються над об'єднанням графів (`use_default_graph_as_union`).

## Префікси

```
PREFIX dkh: <http://example.org/dkh/onto#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
```

Ті самі префікси записано у всіх файлах Turtle (`@prefix dkh:` тощо) і в `scripts/store.py` (`PREFIXES`) — єдине джерело для запитів.

## Завантажені файли й перевірка COUNT

| Граф | Файл | Триплетів (rdflib) | COUNT у сторі | SHA-256 (12) |
|---|---|---|---|---|
| tbox | data/graphs/tbox.ttl | 1382 | 1382 | 2c94060e88c6 |
| abox | data/graphs/abox.ttl | 2438 | 2438 | 4cd5e0d30f05 |
| inferred | data/graphs/inferred.ttl | 520 | 520 | 718af7766f49 |
| links | data/links.ttl | 85 | 85 | 4e7217dca445 |

Запит: `SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }` → **4425** квадів; сума за графами збігається з кількістю триплетів у файлах: **так**.

Додаткова перевірка: `SELECT (COUNT(DISTINCT ?s) …) WHERE { ?s a/rdfs:subClassOf* dkh:GeneticVariant }` → 64 генетичних варіантів (4 з ЛР7 + 60 синтетичних).

## JSON-LD

`data/kb.jsonld` — 69 іменованих індивідів ЛР7 (≥ 20), 377 триплетів; зворотний парсинг rdflib дає 377 триплетів (збігається).

## Збагачення даними

До онтології й індивідів ЛР7 додано синтетичну когорту (seed 42): 3 зразки (SAMPLE-A/B/C), по 20 варіантів із анотаціями QD, FS, SOR, MQ (значення випадкові в правдоподібних діапазонах), три патогенні варіанти, клас `dkh:Sample` і властивість `dkh:fromSample`. Усі особи й варіанти вигадані.
