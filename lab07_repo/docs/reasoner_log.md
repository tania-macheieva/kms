# Журнал reasoner (HermiT)

Дата запуску: 2026-10-26 09:49. Reasoner: HermiT (HermiT.jar із пакета owlready2 0.51); Java: OpenJDK 21.
Онтологія: models/onto.owl + models/onto_data.ttl (злиті rdflib у RDF/XML; Protégé очікує ту саму комбінацію). Скрипт: `python scripts/reasoner_run.py`. Протоколи Protégé (скріншоти) в цьому середовищі отримати неможливо — замість них наведено вивід командного рядка HermiT.

## 1. Узгодженість і класифікація

Команда: `java -cp HermiT.jar org.semanticweb.HermiT.cli.CommandLine -c file:///…/m.owl` → код завершення **0**; необґрунтованих (unsatisfiable) класів: **0**. Онтологія **узгоджена**. Вивід починається так:

```
SubClassOf( <http://example.org/dkh/onto#SecondDegreeRelative> <http://example.org/dkh/onto#Relative> )
SubClassOf( <http://example.org/dkh/onto#AdultRelative> <http://example.org/dkh/onto#Relative> )
SubClassOf( <http://example.org/dkh/onto#MinorRelative> <http://example.org/dkh/onto#Relative> )
SubClassOf( <http://example.org/dkh/onto#ThirdDegreeRelative> <http://example.org/dkh/onto#Relative> )
SubClassOf( <http://example.org/dkh/onto#FirstDegreeRelative> <http://example.org/dkh/onto#Relative> )
SubClassOf( <http://example.org/dkh/onto#OfferCascadeTestingAction> <http://example.org/dkh/onto#Action> )
…
(усього 66 рядків SubClassOf/EquivalentClasses; повний вивід — docs/evidence/hermit_classify.txt)
```

## 2. Виведені твердження про індивідів (класифікація екземплярів, `-I`)

Нових припущень типу (відсутніх у вхідних даних): **18**.

| Індивід | Виведений тип | Чому (аксіома) |
|---|---|---|
| Andrii | AdultRelative | Relative ⊓ ∃hasAgeYears.[≥ 18] |
| Andrii | ThirdDegreeRelative | ланцюг hasAuntOrUncle∘hasChild = hasCousin ⊑ isThirdDegreeRelativeOf |
| Halyna | AdultRelative | Relative ⊓ ∃hasAgeYears.[≥ 18] |
| Halyna | SecondDegreeRelative | ланцюги hasParent∘hasParent, hasParent∘hasSibling ⊑ isSecondDegreeRelativeOf |
| Iryna | AdultRelative | Relative ⊓ ∃hasAgeYears.[≥ 18] |
| Iryna | FirstDegreeRelative | Person ⊓ ∃isFirstDegreeRelativeOf.Proband (зв'язок виведено з hasParent/hasSibling/hasChild) |
| Maria | SecondDegreeRelative | ланцюги hasParent∘hasParent, hasParent∘hasSibling ⊑ isSecondDegreeRelativeOf |
| Marta | AdultRelative | Relative ⊓ ∃hasAgeYears.[≥ 18] |
| Marta | FirstDegreeRelative | Person ⊓ ∃isFirstDegreeRelativeOf.Proband (зв'язок виведено з hasParent/hasSibling/hasChild) |
| Petro | AdultRelative | Relative ⊓ ∃hasAgeYears.[≥ 18] |
| Petro | FirstDegreeRelative | Person ⊓ ∃isFirstDegreeRelativeOf.Proband (зв'язок виведено з hasParent/hasSibling/hasChild) |
| Sofiia | FirstDegreeRelative | Person ⊓ ∃isFirstDegreeRelativeOf.Proband (зв'язок виведено з hasParent/hasSibling/hasChild) |
| Sofiia | MinorRelative | Relative ⊓ ∃hasAgeYears.[< 18] |
| VAR-001 | PathogenicVariant | GeneticVariant ⊓ ∃hasClinicalSignificance.{Pathogenic} |
| VAR-002 | LowQDVariant | ∃hasAnnotation.(QualityByDepth ⊓ значення < 2) |
| VAR-002_QualityByDepth | LowQDAnnotation | QualityByDepth ⊓ значення < 2 |
| VAR-004 | ExonEndVariant | GeneticVariant ⊓ hasExonEndPosition = true |
| VAR-004 | HighFSSnpVariant | SNP ⊓ ∃hasAnnotation.(FisherStrandBias ⊓ значення > 60) |

## 3. Виведені зв'язки між індивідами (`sync_reasoner_hermit(infer_property_values=True)`)

Нових зв'язків: **44**. Приклади:

```
Andrii hasAncestor Maria
Andrii hasAuntOrUncle Iryna
Andrii hasCousin Marta
Andrii hasCousin Olena
Andrii hasGrandparent Maria
Andrii hasParent Halyna
Andrii isSecondDegreeRelativeOf Iryna
Andrii isSecondDegreeRelativeOf Maria
Halyna hasSibling Iryna
Halyna isSecondDegreeRelativeOf Marta
Halyna isSecondDegreeRelativeOf Olena
Iryna hasChild Marta
Iryna hasChild Olena
Iryna isSecondDegreeRelativeOf Andrii
Iryna isSecondDegreeRelativeOf Sofiia
Maria isSecondDegreeRelativeOf Andrii
Maria isSecondDegreeRelativeOf Marta
Maria isSecondDegreeRelativeOf Olena
Marta hasAncestor Maria
Marta hasAuntOrUncle Halyna
Marta hasCousin Andrii
Marta hasGrandparent Maria
Marta isSecondDegreeRelativeOf Halyna
Marta isSecondDegreeRelativeOf Maria
Marta isSecondDegreeRelativeOf Sofiia
…
```

## 4. Навмисні суперечності

### Суперечність 1: індивід VAR-003 (INDEL) додатково оголошено SNP, а SNP і Indel диз'юнктні

Внесена зміна: `VAR-003 rdf:type dkh:SNP`.

HermiT (код завершення 1):

```
Exception in thread "main" org.semanticweb.owlapi.reasoner.InconsistentOntologyException: Inconsistent ontology
	at org.semanticweb.HermiT.Reasoner.throwInconsistentOntologyExceptionIfNecessary(Reasoner.java:2164)
	at org.semanticweb.HermiT.Reasoner.checkPreConditions(Reasoner.java:2154)
```

Усунення: видалено доданий(і) трип­лет(и) (у Protégé — вилучити твердження або виправити тип/кількість батьків); повторний запуск HermiT → код 0, онтологія знову узгоджена.

### Суперечність 2: Marta має трьох різних батьків, а Person ⊑ hasParent ≤ 2

Внесена зміна: `Marta hasParent Maria; Iryna, Petro, Maria — owl:differentFrom`.

HermiT (код завершення 1):

```
Exception in thread "main" org.semanticweb.owlapi.reasoner.InconsistentOntologyException: Inconsistent ontology
	at org.semanticweb.HermiT.Reasoner.throwInconsistentOntologyExceptionIfNecessary(Reasoner.java:2164)
	at org.semanticweb.HermiT.Reasoner.checkPreConditions(Reasoner.java:2154)
```

Усунення: видалено доданий(і) трип­лет(и) (у Protégé — вилучити твердження або виправити тип/кількість батьків); повторний запуск HermiT → код 0, онтологія знову узгоджена.
