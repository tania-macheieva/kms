# Закритий каталог відношень (використовуй ЛИШЕ ці id)

- `is_a` (є різновидом): Вужче поняття є різновидом (підкласом) ширшого; для екземплярів — є прикладом класу. Приклад: hard filtering is_a variant filtering
- `part_of` (є складовою): Об'єкт є частиною цілого (структурно чи функціонально). Приклад: gene part_of gene panel
- `has_annotation` (має показник): Варіант, дані чи сутність характеризуються вимірюваним показником якості. Приклад: genetic variant has_annotation quality by depth
- `increases_risk_of` (підвищує ризик): Генетична сутність або властивість підвищує ймовірність захворювання. Приклад: pathogenic variant increases_risk_of hereditary cancer
- `is_kin_of` (є родичем): Особа перебуває у спорідненості з іншою особою (родич — пробанд). Приклад: relative is_kin_of proband
- `uses_input` (використовує): Процедура чи показник використовує як вхід дані, показник або сутність. Приклад: hard filtering uses_input Fisher strand bias
- `produces` (створює): Процедура створює дані, варіанти чи показники як результат. Приклад: variant calling produces VCF file
- `applies_to` (застосовується до): Процедура чи показник застосовується до об'єкта (дані, варіант, особа). Приклад: cascade testing applies_to relative
- `requires` (потребує): Для виконання процедури необхідна передумова: дані, варіант, інша процедура. Приклад: cascade testing requires pathogenic variant
- `recommended_for` (рекомендований для): Джерело рекомендує процедуру або показник для певного випадку чи об'єкта. Приклад: hard filtering recommended_for gene panel
- `detects` (виявляє): Метод або процедура виявляє варіант, сутність чи стан. Приклад: genetic testing detects pathogenic variant
- `has_example` (має приклад): Поняття має конкретний приклад (екземпляр, порогове значення, випадок). Приклад: quality by depth has_example «QD < 2»
