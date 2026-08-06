# Синтезований контекст

Нижче збережено дев’ять DOC-класифікацій як topic-keyed context. Кожен запис
має attributed synthesis і вибрані verbatim source notes, огороджені
унікальним маркером untrusted data. Повний текст лишається за вказаним
`source` path.

## Four-day upper/lower program

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/README.md
- topic: структура програми, paired-set notation, тижневий schedule і узгоджений weekly volume
- synthesis: Чотириденна upper/lower програма чергує strength і hypertrophy sessions, використовує paired sets для економії часу без перетворення heavy lifts на circuit і за можливості залишає щонайменше 48 годин між lower-body sessions. Overview узгоджено з session prescriptions: 13 mandatory quadriceps sets, до 15 з optional lower-strength block, і 12 core sets.

DATA_c9c0606c_START
```text
Чотириденна програма з paired sets для гіпертрофії, зростання або збереження сили та збереження м’язової маси під час дефіциту калорій.

Дні можна зміщувати, але між двома тренуваннями низу бажано залишати щонайменше 48 годин.

| М’язова група | Робочі підходи на тиждень |
|---|---:|
| Квадрицепс | 13 обов’язкових, до 15 з опціональним блоком |
| Задня поверхня стегна | 9 |
| Сідниці | 9–12 |
| Литки | 6 |
| Кор | 12 |

Це не максимальний обсяг. Для дефіциту й приблизно пів року системного стажу цього достатньо. Спочатку потрібно довести, що відновлення та прогрес можливі на цьому обсязі.
```
DATA_c9c0606c_END

## Upper-strength session

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/01 upper strength.md
- topic: day-one prescription, paired-set timing, RIR і timebox fallback
- synthesis: Session тривалістю 50–60 хвилин пріоритизує barbell bench press, lat pulldown, shoulder press і seated row, поєднує їх з arm work, а lateral raises і face pulls першими скорочуються після 55 хвилин. Warm-up триває 6–8 хвилин.

DATA_3c3451af_START
```text
Орієнтовний час: **50–60 хвилин**.

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| A1. Жим штанги лежачи | 4 × 4–6 | 2 |
| A2. Cable curl | 3 × 8–12 | 2 |

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| B1. Precor lat pulldown | 4 × 5–8 | 1–2 |
| B2. Cable pushdown | 3 × 8–12 | 1–2 |

Якщо минуло 55 хвилин, блок D можна скоротити до одного підходу або пропустити.
```
DATA_3c3451af_END

## Lower-strength session

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/02 lower strength.md
- topic: day-two prescription, 7–8 minute warm-up, recovery-sensitive pairing і optional unilateral volume
- synthesis: Lower-strength day вкладається у 50–60 хвилин і має 7–8 minute warm-up у межах SPEC budget `0–8`. Основні рухи — squat, RDL і leg press; core та calf work підібрані з низькою interference, після RDL дозволений довший rest, а Bulgarian split squat є optional за time/recovery gates.

DATA_a116f97b_START
```text
## Розминка — 7–8 хвилин

- 3–4 хвилини велосипеда або гребного тренажера.
- 1 легкий сет goblet squat.
- 3–4 поступові розминкові сети присідання.

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| A1. Присідання зі штангою | 4 × 4–6 | 2 |
| A2. Pallof press | 3 × 10–15 на бік | 2–3 |

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| C1. Precor leg press | 3 × 6–10 | 2 |
| C2. Cable crunch | 3 × 10–15 | 1–2 |

Додавай цей блок лише якщо:

- тренування вкладається в годину;
- ноги нормально відновлюються;
- силові не падають два тренування поспіль.
```
DATA_a116f97b_END

## Upper-hypertrophy session

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/03 upper hypertrophy.md
- topic: day-three antagonist pairings, hypertrophy ranges і proximity to failure
- synthesis: Upper-hypertrophy day триває 50–58 хвилин і має чотири paired blocks для chest/back, vertical pull/chest isolation, side/rear delts і arms. Rest скорочується від 60–75 до 30–45 seconds; другий arm set може наближатися до failure лише зі стабільною технікою.

DATA_aec52a6c_START
```text
| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| A1. Incline dumbbell press | 3 × 8–12 | 1–2 |
| A2. Precor seated row | 3 × 8–12 | 1–2 |

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| C1. Cable lateral raise | 3 × 12–20 | 0–2 |
| C2. Cable reverse fly | 3 × 12–20 | 0–2 |

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| D1. Cable overhead triceps extension | 2 × 10–15 | 0–2 |
| D2. Hammer curl | 2 × 10–15 | 0–2 |

У другому сеті можна наближатися до відмови, якщо техніка не розвалюється.
```
DATA_aec52a6c_END

## Lower-hypertrophy session

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/04 lower hypertrophy.md
- topic: day-four prescription, unilateral/timed work і fatigue fallback
- synthesis: Lower-hypertrophy day триває 50–60 хвилин та поєднує leg press/calf extension, Bulgarian split squat/cable crunch, moderate RDL/side plank і hip thrust/TRX hamstring curl. Right і left leg рахуються одним set, side plank є duration-based, а final compound pair розділяється, якщо performance різко падає.

DATA_5bd82a0d_START
```text
| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| B1. Bulgarian split squat | 3 × 8–12 на ногу | 1–2 |
| B2. Cable crunch | 3 × 10–15 | 1–2 |

Праву і ліву ногу рахуй як один підхід. Не відпочивай довго між ногами, але можеш взяти 15–30 секунд, щоб відновити дихання.

| Вправа | Підходи × повторення | RIR |
|---|---:|---:|
| C1. Dumbbell або barbell Romanian deadlift | 3 × 8–12 | 1–2 |
| C2. Side plank | 3 × 25–45 с на бік | 2–3 |

Якщо продуктивність різко падає:

1. Виконай усі три сети hip thrust.
2. Потім виконай усі три сети TRX hamstring curl.
```
DATA_5bd82a0d_END

## Confirmed gym-equipment inventory

- source: /home/muuser/bushuk-labs/gym/gym equipment/gym equipment list.md
- topic: equipment availability, quantity, attachments і evidence quality
- synthesis: Інвентар зводить 32 photographs до недубльованих equipment records. Він підтверджує cardio machines, combined pulldown/row, дві близькі cable stations, multi-press, leg press/calf machine, GluteBuilder, rack/barbell/benches, dumbbells 10–75 lb, kettlebells, щонайменше 300 lb plates, bags/balls, TRX, battle rope, attachments, boxes, mats і marked lane. Occluded quantities та unreadable models лишаються uncertain, а не домислюються.

DATA_dd18337a_START
```text
Інвентар складено за 32 фотографіями з папки [`photos gym equipment`](../../gym%20equipment/photos%20gym%20equipment/) та доповнено уточненнями користувача. Повторні ракурси одного й того самого обладнання зведено в один запис. Позначка **«щонайменше»** використана там, де частину ряду або стійки перекрито і точну кількість із фотографій визначити неможливо.

- Інвентар описує все обладнання, яке можна надійно розпізнати на наданих фотографіях; приховані за колонами або обрізані предмети не домислювалися.
- Точну кількість окремих дисків, гир, м’ячів, матів, кабельних насадок і CoreBag неможливо гарантувати через перекриття та повторні ракурси; однак сумарна вага комплекту дисків, за уточненням користувача, становить щонайменше 300 lb.
- Бренди й моделі вказані там, де їх можна прочитати або надійно зіставити з конструкцією виробника. Для жимового Precor точна модель нечитабельна, тому наведено функціональний опис.
```
DATA_dd18337a_END

## Equipment-derived master exercise catalog

- source: /home/muuser/bushuk-labs/gym/gym equipment/all gym exercises.md
- topic: practical movement families, confirmed-equipment boundary і catalog granularity
- synthesis: Master catalog охоплює 24 equipment/modality sections — cardio, selectorized і cable work, rack/barbell, dumbbells, kettlebells, bags, balls, rope, TRX, boxes, bodyweight, agility та mixed complexes. Він відрізняє mechanic changes від темпу/reps/пауз/load/order і виключає вправи, що потребують непідтвердженого equipment.

DATA_7449d724_START
```text
Це майстер-список вправ за наявним обладнанням із [`gym equipment list.md`](../../gym%20equipment/gym%20equipment%20list.md). Тут зібрані практично відмінні вправи й основні варіації хвату, стійки, нахилу та одностороннього виконання. Зміна кількості повторень, темпу, паузи або робочої ваги не рахується новою вправою, якщо механіка руху залишається тією самою.

- Не включені вправи, для яких потрібне відсутнє або не підтверджене обладнання: EZ-гриф, landmine, санчата, спеціальна GHD-лава, leg-extension/leg-curl машина, римський стілець, окремі бруси чи підтверджений комплект еспандерів.
- Cable crossover тут має обмежену ширину через близьке розташування двох установок, але D-руків’я дають змогу виконувати зведення та жими з меншою базою.
- Для кабельних вправ на ноги використовується наявне ремінне кріплення; якщо воно не підходить до щиколотки, відповідні вправи слід пропустити до появи ankle strap.
- «Всі вправи» означає всі практично відмінні сімейства рухів, які випливають із наявного обладнання. Нескінченні комбінації темпу, повторень, пауз, інтервалів і порядку вправ окремими вправами не рахуються.
```
DATA_7449d724_END

## Exercise taxonomy

- source: /home/muuser/bushuk-labs/gym/gym equipment/exercise categories.md
- topic: primary muscle, movement pattern, physical quality, equipment і placement rules
- synthesis: Taxonomy класифікує вправи за main purpose, зберігаючи secondary attributes. Вона визначає muscle-group, movement-pattern і physical-quality codes, equipment groups та placement rules для unilateral, tempo, isometric, cardio, agility й compound movements.

DATA_4db08cab_START
```text
Одна вправа може навантажувати кілька груп, але в категоризованому списку вона розміщується передусім за **головною метою**. Другорядні м’язи або якості зазначаються в дужках, щоб не створювати десятки непотрібних дублікатів.

1. Багатосуглобова вправа розміщується за головним рушієм: bench press — груди, squat — квадрицепс, RDL — задня поверхня стегна, hip thrust — сідниці.
2. Якщо вправа однаково виражено тренує кілька зон, вона може повторюватися в двох категоріях із приміткою про іншу роль.
3. Односторонні версії не утворюють окрему м’язову категорію; вони отримують додаткову ознаку `BALANCE` або `ANTI-ROTATION`.
4. Варіації темпу, паузи та ізометрії залишаються поруч із базовою вправою.
5. Кардіо- і спритнісні вправи класифікуються за фізичною якістю, навіть якщо активно навантажують ноги.
6. Комплекси з кількох рухів належать до `FULL BODY / POWER / CONDITIONING`, а їхні окремі складові залишаються у відповідних м’язових категоріях.
```
DATA_4db08cab_END

## Curated exercise-selection reference

- source: /home/muuser/bushuk-labs/gym/gym equipment/exercises by category.md
- topic: canonical families, programming suitability, substitutions, limitations і verification status
- synthesis: Curated reference консолідує near-duplicate variants у canonical exercise families, фіксує setup/equipment limitations, preferred strength/hypertrophy roles, substitutions і verification status. Final matrix оцінює suitability, rep range, RIR і fatigue cost, але не задає complete program.

DATA_740a89e9_START
```text
Структурований довідник вправ, підтверджених фотографіями спортзалу, [`gym equipment list.md`](../../gym%20equipment/gym%20equipment%20list.md) і попередньою версією цього файла. Він призначений для подальшого добору вправ до `Upper Strength`, `Lower Strength`, `Upper Hypertrophy` і `Lower Hypertrophy`, але не є готовою тренувальною програмою.

Окремим записом вважається практично відмінна механіка. Зміни хвату, темпу, паузи, стійки, односторонності або кута наведені в `Setup notes`, щоб не створювати дублікати. `Confirmed` означає, що обладнання й базова конфігурація підтверджені. `Needs verification` означає, що перед використанням треба перевірити сумісність насадки, геометрію, стійкість, правила залу або безпечну амплітуду.

- Exercises requiring resistance bands, a landmine, EZ-bar, parallel dip bars, GHD/45-degree back-extension bench, gymnastic rings, dedicated leg-extension/leg-curl machine or a confirmed ankle cuff are not treated as confirmed primary options.
- No decline bench capability is assumed.
- No treadmill sideways/backward drills are recommended.
- No bar-dropping, wall-ball target or dedicated Olympic-lifting platform is assumed.

The matrix rates suitability for a future strength-focused or hypertrophy-focused day; it does not prescribe exercise order, weekly volume or a complete program.
```
DATA_740a89e9_END
