See [ChangeLog](/ChangeLog.md) для найсвіжіших оновлень.<br>
Приєднуйтеся до discord, якщо потрібна підтримка або хочете запропонувати нові функції:  https://discord.gg/HCgkfSc
<br>

# Основні можливості ED Autopilot
Цей Elite Dangerous (ED) Autopilot підтримує такі основні можливості:
## FSD Route assist
Для FSD Route Assist виберіть пункт призначення у GalaxyMap, увімкніть цей асистент — і він виконає всі стрибки, щоб доставити вас до цілі, AFK. Крім того,
під час виконання маршруту він виконуватиме детальне сканування системи (honk) після кожного стрибка та за потреби виконуватиме FSS-сканування,
щоб визначити, чи є світи Earth, Water або Ammonia.
## Supercruise assist
Supercruise (SC) assistant (на відміну від SC Assist гри, що займає слот)
утримуватиме ціль, і коли з’явиться «TO DISENGAGE», автоматично вийде з SC і виконає autodocking з вибраною станцією. <br>
## Waypoint assist
З Waypoint Assist ви задаєте маршрут у файлі, і асистент стрибатиме за цими waypoint. Якщо визначено Station для docking,
асистент переключиться на SC Assist і
пришвартується до станції. Також включено ранню версію функції торгівлі.<br>
Додаткову інформацію можна знайти [тут](docs/Waypoint.md).
## Robigo Mines assist
Robigo Assist виконує цикл passenger-місій Robigo Mines, включно з вибором місій, завершенням місій та
повним циклом до Sirius Atmospherics.<br>
Додаткову інформацію можна знайти [тут](docs/Robigo.md).
## AFK Combat escape assist
## Single Waypoint assist
Примітка: наразі доступно на вкладці debug.

З Single Waypoint Assist ви вводите цільову систему в текстове поле (вставте з Inara/Spansh тощо) і ставите checkbox,
щоб побудувати маршрут і виконати стрибки до цієї system.<br>

# Додаткові можливості
## Voice
Якщо Voice увімкнено, автопілот повідомлятиме про свої дії.

## Інтеграція з TCE (Trade Computer Extension)
Базова інтеграція з TCE. Поточний пункт призначення TCE можна завантажити як ціль для Single Waypoint Assist кнопкою Load TCE Destination на вкладці Debug.
Деталі про TCE дивіться у [теми TCE на форумі Frontiers](https://forums.frontier.co.uk/threads/trade-computer-extension-mk-ii.223056/).

Цей автопілот використовує Computer Vision (захоплює екрани та виконує зіставлення шаблонів) і надсилає натискання клавіш. Він не виконує
жодних runtime-змін
Elite Dangerous, це зовнішній щодо ED компонент (подібно до нас, командирів).

  ```
  ./docs
  * Calibration.md — як відкалібрувати EDAPGui для вашої системи за потреби
  * Waypoint.md — як створити файл waypoint
  * RollPitchYaw.md — як налаштувати значення Pitch, Roll, Yaw
  * Robgio.md — подробиці циклу Robigo Mines
  ```

Примітка: цей автопілот базується на https://github.com/skai2/EDAutopilot , деякі процедури використано й перетворено на класи,
а також налаштовано послідовності та методи зіставлення зображень. Подяка skai2mail@gmail.com

Ще одна примітка: цей репозиторій надано для освітніх цілей як розгорнутий приклад програмування взаємодії з файловими даними,
оброблення зображень, зворотного зв’язку через voice, інтеграції win32 у python, взаємодії потоків і python-класів.

# Обмеження:
* Працює лише в Windows (не Linux)
* Потрібно використовувати стандартні кольори HUD; якщо ви їх зміните, автопілот не працюватиме
* Потрібна конфігурація Elite Dangerous (ED) Borderless; Windowed не працює через спосіб захоплення екрана
* Роздільна здатність/масштаб екрана X, Y: шаблони створено на конфігурації з роздільною здатністю 3440x1440. Їх необхідно масштабувати
  для інших роздільних здатностей. Файл _config-resolution.json_ містить ці роздільні здатності з відповідними значеннями ScaleX, Y. Якщо роздільну здатність не визначено
  для вашого монітора, код спробує поділити на /3440 та /1440, щоб отримати коефіцієнт масштабування (ймовірно, неточно)
  ```
  * Див. docs/Calibration.md, щоб дізнатися, як відкалібрувати EDAPGui для вашої системи *
  ```
  * Налаштування Field of View (Graphics->Display) важливе. Я використовую близько 10-15% на шкалі. Якщо у вас великий FOV,
    шаблонні зображення, імовірно, будуть завеликі
* Фокус: під час роботи ED має бути у фокусі, тому не можна працювати з іншими вікнами, поки AP активний.
           Якщо змінити фокус, клавіатурні події надсилатимуться у вибране вікно, що може зіпсувати
           це вікно
* Control Rates: потрібно вказати швидкості roll, pitch, yaw для вашого корабля. Дивіться HOWTO-RollPitchYaw.md, почніть зі значень із Outfitting для свого корабля
* Autodocking: щоб AP розпізнав «TO DISENGAGE», неважливо, до якої клавіші прив’язано цю дію.
* Routing: під час використання Economical Route можуть виникнути проблеми зі стрибками. За Economical зірки можуть не бути на «іншому боці»
  Sun, як при Fastest.
  Тож під час roll у напрямку Target Sun може засвітити консоль, ускладнивши зіставлення Compass. Треба ще продумати це. Світло від Sun
  вбиває зіставлення. Це видно, якщо увімкнути CV View
* Left Panel (Navigation) має бути на вкладці Navigation, як очікує скрипт. Після стрибка FSD вона повернеться до Nav,
  але в SC Assist потрібно переконатися, що вкладка налаштована для підтримки docking request
* Модуль «Advanced Autodocking» має бути встановлено на корабель для підтримки autodock
* ELW Scanner може працювати неідеально: screen region (визначена у Screen_Region.py) виділяє область, де будуть сигнали Earth, Water та Ammonia.
  Якщо використовуєте роздільну здатність, відмінну від 3440x1440, цю область потрібно скоригувати для вашої роздільної здатності,
  щоб визначення працювало
* Необхідно мати потрібні keybinding для коректної роботи автопілота. Дивіться autopilot.log щодо попереджень про відсутні прив’язки
* Якщо стрибнути в систему з двома suns поруч, імовірно, корабель перегріється і вийде з Supercruise.
* Бували випадки, коли після дозаправлення, залежно від розгону корабля, ми не відлітаємо від Sun достатньо далеко перед увімкненням FSD,
  і можемо перегрітися

# Встановлення
_Потрібні **python 3** і **git**_

_Python 3.11 — рекомендована версія. Можна використовувати Python 3.9 або 3.10._
Якщо у вас не встановлено Python, ось посилання на [інсталятор Python 3.11](https://www.python.org/downloads/release/python-3110/). Прокрутіть униз і виберіть інсталятор із позначкою «Recommended».

## Простий варіант
Якщо ви лише хочете завантажити й запустити EDAP і не цікавитеся вихідним кодом, скористайтеся цим методом:

1. Завантажте джерело, натиснувши зелену кнопку '<> Code' вище, а потім «Download ZIP».
2. Розпакуйте zip у будь-яку папку.
3. Знайдіть файл 'start_ed_ap.bat' у папці.
4. Двічі клацніть (запустіть) файл 'start_ed_ap.bat'.
5. Інсталяція має розпочатися, завантажити всі необхідні файли й завершитися.
6. Двічі клацніть (запустіть) файл 'start_ed_ap.bat' знову, щоб стартувати EDAP.

## Розширений варіант
Якщо ви цікавитеся Python і хочете вносити зміни в код або подивитися, як він працює, скористайтеся цим методом:

1. Клонуйте репозиторій
```sh
git clone https://github.com/Vova-Bob/EDAPGui
```
2. Встановіть залежності
```sh
cd EDAPGui
pip install -r requirements.txt
```
або запустіть 'install_requirements.bat':
```sh
cd EDAPGui
install_requirements.bat
```
3. Запустіть скрипт
```sh
python EDAPGui.py
АБО можливо доведеться виконати
python3 EDAPGui.py
якщо встановлено і python 2, і 3.
```

Якщо під час pip install виникають проблеми, спробуйте виконати:
> python -m pip install -r requirements.txt
замість > pip install -r requirements.txt

Може з’явитися така помилка:
> AttributeError: '_thread._local' object has no attribute 'srcdc'

Зазвичай ця помилка пов’язана з несумісністю mss. Спробуйте pip install mss==8.0.3 або pip install mss==8.0.3.

# Запуск ED_AP
* Коли Elite Dangerous (ED) запущено, стартуйте ED_AP:
    * Подвійним кліком на start_ed_ap.bat у Windows Explorer (бажаний спосіб).
    * Ввівши 'python EDAPGui.py' у консольному вікні.
    * Запустивши EDAPGui.py безпосередньо в IDE з підтримкою Python.
* Має з’явитися ED_AP Gui, і в log можуть бути повідомлення з попередженнями про проблеми, які потрібно усунути. Деталі щодо їх вирішення є на цій сторінці.

# Початок роботи
Після запуску ED_AP потрібно виконати кілька кроків при першому старті, щоб уникнути поширених проблем.
1. Виконайте калібрування екрана — деталі [тут](docs/Calibration.md). Це налаштує ED_AP під вашу роздільну здатність. Багатьох проблем можна уникнути правильним калібруванням.
2. Перевірте та за потреби змініть параметри keybinding, описані нижче. Особливо переконайтеся, що клавіші Ins, Home, End і Pg Up не використовує ED, бо їх застосовує EDAP.
3. Примітка: файл autopilot.log фіксуватиме всі необхідні прив’язки, яких бракує.
4. Виберіть правильний файл корабля, що відповідає вашому кораблю — це налаштує швидкості pitch, roll і yaw. Залежно від корабля, можливо, доведеться підлаштувати значення для найкращої реакції — детально [тут](docs/RollPitchYaw.md).
5. Виконайте тест у межах системи:
    * В ED скористайтеся Left Panel, щоб вибрати локальний target.
    * В автопілоті увімкніть SC Assist або натисніть 'Ins'.
    * Коли асистент стартує, він переключить фокус на вікно Elite Dangerous.
    * Корабель виконає undock (якщо пришвартований), перейде в SC, вийде на target і після прибуття спробує пришвартуватися, якщо це станція.
    * Якщо виникають проблеми з польотом, перевірте налаштування корабля.
6. Виконайте тест поза системою:
   * В ED на Galaxy Map виберіть цільову систему.
   * В автопілоті увімкніть FSD Assist або натисніть 'Home'.
   * Коли асистент стартує, він переключить фокус на вікно Elite Dangerous.
   * Корабель виконає undock (якщо пришвартований), перейде в SC, вийде на target, виконає стрибок FSD. Прибувши в систему, облетить star, виконає fuel scoop за потреби й або зупиниться, якщо внутрішньосистемна ціль не вибрана, або спробує долетіти до target і пришвартуватися, якщо це станція.
   * Якщо виникають проблеми з польотом, перевірте налаштування корабля.


# Потрібні keybinding
Наступні keybinding потрібні для AP, тож переконайтеся, що кожна з них призначена в налаштуваннях Elite Dangerous. Після зміни keybinding знову запустіть AP, щоб він прочитав зміни. Якщо будь-яку прив’язку пропущено, з’явиться помилка.

| Binding               | Name                     | Location under OPTIONS > CONTROLS            |
|-----------------------|--------------------------|----------------------------------------------|
| UI_Up                 | UI PANEL UP              | GENERAL CONTROLS > INTERFACE MODE            |
| UI_Down               | UI PANEL DOWN            | GENERAL CONTROLS > INTERFACE MODE            |
| UI_Left               | UI PANEL LEFT            | GENERAL CONTROLS > INTERFACE MODE            |
| UI_Right              | UI PANEL RIGHT           | GENERAL CONTROLS > INTERFACE MODE            |
| UI_Select             | UI PANEL SELECT          | GENERAL CONTROLS > INTERFACE MODE            |
| UI_Back               | UI Back                  | GENERAL CONTROLS > INTERFACE MODE            |
| CycleNextPanel        | NEXT PANEL TAB           | GENERAL CONTROLS > INTERFACE MODE            |
|                       |                          |                                              |
| MouseReset            | RESET MOUSE              | SHIP CONTROLS > MOUSE CONTROLS               |
|                       |                          |                                              |
| YawLeftButton         | YAW LEFT                 | SHIP CONTROLS > FLIGHT ROTATION              |
| YawRightButton        | YAW RIGHT                | SHIP CONTROLS > FLIGHT ROTATION              |
| RollLeftButton        | ROLL LEFT                | SHIP CONTROLS > FLIGHT ROTATION              |
| RollRightButton       | ROLL RIGHT               | SHIP CONTROLS > FLIGHT ROTATION              |
| PitchUpButton         | PITCH UP                 | SHIP CONTROLS > FLIGHT ROTATION              |
| PitchDownButton       | PITCH DOWN               | SHIP CONTROLS > FLIGHT ROTATION              |
|                       |                          |                                              |
| ThrustUpButton        | THRUST UP                | SHIP CONTROLS > FLIGHT THRUST                |
|                       |                          |                                              |
| SetSpeedZero          | SET SPEED TO 0%          | SHIP CONTROLS > FLIGHT THROTTLE              |
| SetSpeed50            | SET SPEED TO 50%         | SHIP CONTROLS > FLIGHT THROTTLE              |
| SetSpeed100           | SET SPEED TO 100%        | SHIP CONTROLS > FLIGHT THROTTLE              |
|                       |                          |                                              |
| UseBoostJuice         | ENGINE BOOST             | SHIP CONTROLS > FLIGHT MISCELLANEOUS         |
| HyperSuperCombination | TOGGLE FRAME SHIFT DRIVE | SHIP CONTROLS > FLIGHT MISCELLANEOUS         |
| Supercruise           | SUPERCRUISE              | SHIP CONTROLS > FLIGHT MISCELLANEOUS         |
|                       |                          |                                              |
| SelectTarget          | SELECT TARGET AHEAD      | SHIP CONTROLS > TARGETING                    |
|                       |                          |                                              |
| PrimaryFire           | PRIMARY FIRE             | SHIP CONTROLS > WEAPONS                      |
| SecondaryFire         | SECONDARY FIRE           | SHIP CONTROLS > WEAPONS                      |
| DeployHardpointToggle | DEPLOY HARDPOINTS        | SHIP CONTROLS > WEAPONS                      |
|                       |                          |                                              |
| DeployHeatSink        | DEPLOY HEATSINK          | SHIP CONTROLS > COOLING                      |
|                       |                          |                                              |
| IncreaseEnginesPower  | DIVERT POWER TO ENGINES  | SHIP CONTROLS > MISCELLANEOUS                |
| IncreaseWeaponsPower  | DIVERT POWER TO WEAPONS  | SHIP CONTROLS > MISCELLANEOUS                |
| IncreaseSystemsPower  | DIVERT POWER TO SYSTEMS  | SHIP CONTROLS > MISCELLANEOUS                |
| LandingGearToggle     | LANDING GEAR             | SHIP CONTROLS > MISCELLANEOUS                |
|                       |                          |                                              |
| UIFocus               | UI FOCUS                 | SHIP CONTROLS > MODE SWITCHES                |
| GalaxyMapOpen         | OPEN GALAXY MAP          | SHIP CONTROLS > MODE SWITCHES                |
| SystemMapOpen         | OPEN SYSTEM MAP          | SHIP CONTROLS > MODE SWITCHES                |
| ExplorationFSSEnter   | ENTER FSS MODE           | SHIP CONTROLS > MODE SWITCHES                |
|                       |                          |                                              |
| HeadLookReset         | RESET HEADLOOK           | SHIP CONTROLS > HEADLOOK MODE                |
|                       |                          |                                              |
| ExplorationFSSQuit    | LEAVE FSS                | SHIP CONTROLS > FULL SPECTRUM SYSTEM SCANNER |



# Параметри Autopilot:
* FSD Route Assist: виконає ваш маршрут. На кожному стрибку послідовність виконуватиме певний fuel scooping, але якщо
    рівень пального падає нижче порогу, послідовність зупиниться біля Star, доки дозаправлення не завершиться.
    Якщо дозаправлення не завершується за 35 секунд, послідовність переривається й переходить до наступного пункту. Якщо паливо падає нижче
    10% (налаштовується), route assist завершиться
* Supercruise Assist: утримує корабель на target. Ціллю має бути станція, щоб працювало autodocking.
    Якщо target — settlement або ціль перекрита, ви вийдете з SC
    через "Dropped Too Close" або "Dropping from Orbital Cruise" (без пошкоджень), throttle буде встановлено
    на Zero, і SC Assist завершиться. Якщо ж з’являється 'TO DISENGAGE', SC Assist виведе корабель із SC
    та спробує надіслати request docking (після підльоту ближче до Station); якщо docking схвалено,
    встановить throttle 0, і autodocking computer перебере управління. Після docking автоматично виконає refuel і перейде в StarPort Services.
    Примітка: у SC включено реакцію на interdictor. Також під час підльоту до станції, якщо Station перекрита,
    асистент облетить planet і продовжить docking
* Waypoint Assist: при виборі запропонує файл waypoint. Файл waypoint містить назви System для
    введення в Galaxy Map і побудови маршруту. Якщо останній запис у файлі — "REPEAT", цикл почнеться знову.
    Якщо запис waypoint містить Station/StationCoord, асистент прокладе курс до цієї станції
    після входу в систему. Асистент виконає autodock, refuel і repair. Якщо визначено послідовність торгівлі, вона
    буде виконана. Див. HOWTO-Waypoint.md
* Robigo Assist: виконує passenger-місії Robigo Mines. Див. Robigo.md у каталозі docs
* AFK Combat Assist: використовується з AFK Combat ship у Rez Zone. Виявляє падіння shields,
    після чого boost відлітає та переходить у supercruise приблизно на 10 секунд… потім виходить, розподіляє pips на
    system і weapons, випускає fighter, а потім завершує роботу. Під час перебування у Rez Zone, якщо ваш fighter знищено,
    випустить інший (передбачається дві bays)
* ELW Scanner: виконує FSS-сканування під час польотів FSD Assist між зорями. Якщо FSS
    показує сигнал у діапазоні світів Earth, Water чи Ammonia, повідомить про знахідку
    й запише її в elw.txt. Примітка: скан FSS не виконується повністю — потрібно завершити FSD Assist
    й вручну провести докладне FSS-сканування, щоб отримати кредит. Або поверніться пізніше до elw.txt
    і відвідайте ці системи для додаткового сканування. Файл elw.txt виглядає так:<br>
      _Oochoss BL-M d8-3  %(dot,sig):   0.39,   0.79 Ammonia date: 2022-01-22 11:17:51.338134<br>
       Slegi BG-E c28-2  %(dot,sig):   0.36,   0.75 Water date: 2022-01-22 11:55:30.714843<br>
       Slegi TM-L c24-4  %(dot,sig):   0.31,   0.85 Earth date: 2022-01-22 12:04:47.527793<br>_
* Calibrate: перебирає набір значень масштабування, щоб знайти найкраще для вашої системи. Див. HOWTO-Calibrate.md
* Cap Mouse X, Y: надає значення StationCoord для Station у SystemMap. Виберіть кнопку,
    а потім клацніть Station у SystemMap — отримаєте координати x,y, які можна вставити у файл waypoints
* Поле SunPitchUp+Time призначене для кораблів, схильних до перегріву. Додаткові 1-2 секунди Pitch up під час уникнення Sun
    допоможуть. Значення унікальне для корабля й зберігається разом зі значеннями Roll, Pitch, Yaw
* Menu
  * Open : прочитати файл зі значеннями roll, pitch, yaw для корабля
  * Save : зберегти значення roll, pitch, yaw і sunpitchup time у файли
  * Enable Voice : увімкнути/вимкнути voice
  * Enable CV View: увімкнути/вимкнути debug images, що показують процес зіставлення. Показані числа
    відображають % відповідності та поріг. Приклад: 0.55 > 0.5 означає 55% збіг, критерій > 50%, тож збіг істинний

## Гарячі клавіші (можна змінити)
* Home — старт FSD Assist
* Ins  — старт SC Assist
* Pg Up — старт Robigo Assist
* End  — завершення будь-яких активних асистентів

Гарячі клавіші тепер задаються у файлі config-AP.json, тож ви можете переназначити їх. Головне — не використовувати клавіші, які вже задіяні в ED. Список назв клавіш: https://pythonhosted.org/pynput/keyboard.html

## Config-файл: config-AP.json
Наступні налаштування з AP.json **недоступні** через GUI й мають змінюватися безпосередньо в AP.json:
  ```py
    "Robigo_Single_Loop": False,   # True означає виконати лише один цикл, після docking завершити, без оброблення місій
    "EnableRandomness": False,     # додати додаткові випадкові sleep (0-3 сек у певних місцях), щоб уникнути виявлення AP
    "OverlayTextFont": "Eurostyle",
    "OverlayGraphicEnable": False, # ще не реалізовано
    "DiscordWebhook": False,       # інтеграцію з discord ще не реалізовано
    "DiscordWebhookURL": "",
    "DiscordUserID": "",
    "VoiceID": 1,                  # у моїй Windows визначено лише 3 (0-2)
    "FCDepartureTime": 30.0,       # Під час виходу з Fleet Carrier — час у секундах, щоб відлетіти перед увімкненням SC.
    "Language": "en"               # Мова для OCR-перевірок (наприклад 'en', 'fr', 'de')
```
Налаштування `VoiceLanguage`, `UkrainianNeuralTTS` і `UAVoice` тепер можна змінювати через розділ «Голос» у GUI (окремо від мови OCR/UI).

### Опційний нейронний український голос
* Основний проєкт (GUI + автопілот + OCR) працює у звичайному середовищі без `ukrainian-tts`; за замовчуванням використовується pyttsx3.
* Нейронний синтез працює через окремий міст `ua_tts_server.py`, який потрібно запустити в **іншому** віртуальному середовищі з установленим `ukrainian-tts`.
* Кроки для активації мосту:
  1. Створіть окреме venv та встановіть у нього `ukrainian-tts` з усіма залежностями (`pip install ukrainian-tts`).
  2. Запустіть у цьому середовищі сервер: `python ua_tts_server.py` (слухає `http://127.0.0.1:8765/speak`).
  3. У головному GUI ввімкніть Voice, виставте `VoiceLanguage: "uk"`, увімкніть `UkrainianNeuralTTS`, за потреби задайте `UAVoice`, і (за потреби) відкоригуйте `UATTSBridgeURL` у `configs/AP.json`.
* Якщо міст недоступний або повертає помилку, система автоматично повернеться до pyttsx3 без впливу на інші функції.
* Використовується бібліотека [ukrainian-tts](https://github.com/robinhad/ukrainian-tts) лише на боці мосту.

## Elite Dangerous, рольова гра та автопілот
* Я — CMDR у всесвіті Elite Dangerous і маю надійний Diamondback Explorer
* Під час подорожей у глибокий космос я втомився від можливостей свого бортового комп’ютера. Не хочу годинами вручну уникати Sun тільки для стрибка в наступну систему.
* Якщо коротко, Lakon Spaceways бракує бачення. Вони дають Autopilot для docking, undocking і Supercruise, але не можуть зробити
  простий route AP? Ну й справи
* У мене є особистий квантовий обчислювальний пристрій (близько 10 TeraHz CPU, 15 Petabyte RAM) розміром із кредитку з можливістю обробки зображень і взаємодії з моїм Diamondback Explorer Flight Computer,
  тож я розроблю власний автопілот. Це підпадає під «право споживача на вдосконалення», ухвалене законом у 3301 році й ратифіковане всіма галактичними силами
* Тож, CMDRs, вдосконалюймо наші кораблі, щоб ми могли поспати та займатися справами замість годин маневрування навколо Suns

## ПОПЕРЕДЖЕННЯ:

Використовуйте на власний ризик. З цим автопілотом виконано понад 2000 стрибків FSD, і FSD Assist довелося переривати
приблизно 6 разів через стрибки в систему з двома suns поряд, коли корабель перегрівався
і виходив із supercruise. Корабель не було знищено, але довелося використати heat sink, щоб вийти із ситуації

# Контакт електронною поштою

sumzer0@yahoo.com


# Знімки екрана
![Alt text](screen/screen_cap_main.png?raw=true "Main Tab")
![Alt text](screen/screen_cap_settings.png?raw=true "Settings Tab")
![Alt text](screen/screen_cap_debug.png?raw=true "Debug Tab")

