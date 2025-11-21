# StatusParser — читання Status.json та використання флагів

## Зчитування файлу та кеш поточного стану
- **Ініціалізація**: `StatusParser.__init__` приймає шлях до Status.json, запам’ятовує час модифікації, і одразу зчитує перші дані у `self.current_data`, паралельно зберігаючи їх у `self.last_data` для подальших порівнянь змін. 【F:StatusParser.py†L26-L42】
- **Оновлення**: `get_cleaned_data()` перевіряє зміну mtime, читає JSON із резервними спробами, і збирає нормалізований словник з полями `Flags`, `Flags2`, `GuiFocus`, `Destination_*`, паливом тощо. Після кожного успішного читання воно зрушує кеш (`last_data = current_data`, `current_data = cleaned_data`, `last_mod_time` оновлюється). 【F:StatusParser.py†L231-L352】【F:StatusParser.py†L341-L352】

## Доступ до Flags / Flags2
- **Бінарні поля**: базові біти `Flags` та `Flags2` розшифровуються допоміжними `translate_flags`/`translate_flags2`, але в робочому коді автопілот використовує числові константи з `EDAP_data.py` через прямі біти у `current_data`. 【F:StatusParser.py†L104-L184】
- **Гетери**: поточний стан перевіряється методами `get_flag(flag)` та `get_flag2(flag)`; обидва перед викликом оновлюють кеш через `get_cleaned_data()`. 【F:StatusParser.py†L487-L507】
- **Очікування події**: методи `wait_for_flag_on/off` і `wait_for_flag2_on/off` виконують опитування файлу до таймауту, повертаючи `True`, коли біт увімкнувся/вимкнувся. 【F:StatusParser.py†L413-L486】

## Ключові флаги для FSD та Supercruise
- **FSD стан**: `FlagsFsdCharging`, `FlagsFsdJump`, `FlagsFsdCooldown` (Flags) та `Flags2FsdHyperdriveCharging` (Flags2) використовуються в циклі стрибка `jump()`: автопілот чекає початку зарядки, старту стрибка й завершення анімації, а також контролює Hyperdrive Charging через Flags2 для інтердикційного скидання швидкості. 【F:ED_AP.py†L2063-L2104】【F:ED_AP.py†L1158-L1185】
- **Mass lock**: `FlagsFsdMassLocked` використовується при виході з доку або планети, щоб не переходити у SC, доки маслок не знятий (циклічне очікування з бустами). 【F:ED_AP.py†L2233-L2353】
- **Суперкруїз**: `FlagsSupercruise` перевіряється під час безпечних тестів керування кораблем (пітч/рол/риск), а також при спробі вирівнювання у SC, щоб підтвердити поточний режим. 【F:ED_AP.py†L2524-L2586】【F:ED_AP.py†L3027-L3065】
- **SCO/Overcharge**: `Flags2FsdScoActive` у `_sc_sco_active_loop` визначає активність Supercruise Overcharge; при його ввімкненні додається захист від перегріву (`FlagsOverHeating`) та низького палива (`FlagsLowFuel`). 【F:ED_AP.py†L1531-L1569】

## Флаги небезпеки та перехоплення
- **Being Interdicted**: `FlagsBeingInterdicted` тригерить `interdiction_check()`. Якщо біт увімкнений, автопілот подає голосове/лог-повідомлення, тримає швидкість 0 у SC або при зарядці FSD (`FlagsSupercruise` чи `Flags2FsdHyperdriveCharging`), чекає `FlagsFsdCooldown`, бустить до завершення кулдауну та змушує корабель знову увійти у SC (`FlagsFsdJump`). Після втечі скидає `ship_state()['interdicted']`. 【F:ED_AP.py†L1144-L1185】
- **IsInDanger/інші**: флаг `FlagsIsInDanger` зчитується StatusParser’ом, але в поточній логіці не використовується безпосередньо; основні реакції на небезпеку базуються саме на `FlagsBeingInterdicted`.

## Де перевіряються загрози
`interdiction_check()` викликається у кількох довгих циклах, щоб негайно реагувати на перехоплення:
- Під час обходу сонця для уникнення перегріву (`sun_avoid`) — при спрацюванні інтердикції після виходу з петлі корабель зупиняється перед продовженням. 【F:ED_AP.py†L1683-L1714】
- При паливному заправленні (`refuel`) — якщо під час чекання початку/завершення заправлення з’являється інтердикція, автопілот скидає швидкість і потім продовжує. 【F:ED_AP.py†L2164-L2207】
- У Supercruise Align Loop (`sc_assist`) — після кожного кроку вирівнювання в SC виклик перевірки дозволяє перехопленню перервати цикл, після чого автопілот відновлює курс (встановлює 50% та викликає `nav_align`). 【F:ED_AP.py†L2524-L2578】

## Використання флагів в інших модулях
- `EDWayPoint` використовує `FlagsDocked` через `get_flag()` для визначення, чи вже причалили до потрібної станції під час обробки маршруту. 【F:EDWayPoint.py†L675-L699】

## Підсумок по стану StatusParser
- Поточний знімок Status.json зберігається у `current_data`, попередній — у `last_data`; доступні інтерфейси `get_flag*`/`wait_for_flag*` абстрагують бітові перевірки та періодичне опитування файлу. FSD/SC і небезпечні стани (`FsdCharging`, `FsdJump`, `FsdCooldown`, `FsdMassLocked`, `Supercruise`, `FsdScoActive`, `BeingInterdicted`) активно застосовуються в `ED_AP` для стрибків, виходу в SC, маслок-очікувань і оборонної логіки при перехопленнях.
