# Waypoints
Waypoints — це системи, які зберігаються у файлі waypoints.json і зчитуються та опрацьовуються цим Autopilot. Приклад waypoint-файлу наведено нижче:

```py
{
  "1": {
    "SystemName": "Mylaifai EP-G c27-631", "StationName": "", "GalaxyBookmarkType": "", "GalaxyBookmarkNumber": 0, "SystemBookmarkType": "", "SystemBookmarkNumber": 0, "SellCommodities": {}, "BuyCommodities": {}, "UpdateCommodityCount": false, "FleetCarrierTransfer": false, "Skip": false, "Completed": false
  },
  "2": {
    "SystemName": "Striechooe QR-S b37-0", "StationName": "", "GalaxyBookmarkType": "", "GalaxyBookmarkNumber": 0, "SystemBookmarkType": "", "SystemBookmarkNumber": 0, "SellCommodities": {}, "BuyCommodities": {}, "UpdateCommodityCount": false, "FleetCarrierTransfer": false, "Skip": false, "Completed": false
  },
  "3": {
    "SystemName": "Ploxao JV-E b31-1", "StationName": "", "GalaxyBookmarkType": "", "GalaxyBookmarkNumber": 0, "SystemBookmarkType": "", "SystemBookmarkNumber": 0, "SellCommodities": {}, "BuyCommodities": {}, "UpdateCommodityCount": false, "FleetCarrierTransfer": false, "Skip": false, "Completed": false
  },
  "4": {
    "SystemName": "Beagle Point", "StationName": "", "GalaxyBookmarkType": "", "GalaxyBookmarkNumber": 0, "SystemBookmarkType": "", "SystemBookmarkNumber": 0, "SellCommodities": {}, "BuyCommodities": {}, "UpdateCommodityCount": false, "FleetCarrierTransfer": false, "Skip": false, "Completed": false
  }
}
```

З цим waypoint-файлом Autopilot доправить вас до Beagle Point без вашого втручання. Autopilot читатиме
та опрацьовуватиме кожен рядок, прокладаючи курс до **SystemName** у Galaxy Map і виконуючи маршрут через FSD Route
Assist. Коли ви входите до системи, якщо **StationName** не визначено (тобто ''), асистент прокладе маршрут до наступного
рядка у waypoint-файлі. Waypoint-файл зчитується під час вибору Waypoint Assist. Досягнувши фінального
waypoint, Autopilot перейде в режим очікування. Waypoint Assist записує у waypoints.json, позначаючи системи,
які відвідано, встановлюючи для Completed значення true.

## Редактор Waypoint
Найпростіший спосіб налаштувати waypoint-файл — скористатися інструментом Waypoint Editor (зі встановлювачем), написаним на C#, доступним тут: [EDAP-Waypoint-Editor](https://github.com/Stumpii/EDAP-Waypoint-Editor). Згодом ці можливості буде додано до ED_AP.

## Повторення Waypoints
Набір waypoints можна повторювати безкінечно, додавши спеціальний рядок наприкінці waypoint-файлу з назвою системи **'REPEAT'**. Досягнувши цього запису і якщо **Skip** не дорівнює ture, Waypoint Assist почне з початку та виконуватиме переходи між зазначеними системами, доки користувач не завершить Waypoint Assist.

## Docking зі станцією
Під час входу в систему через Waypoint Assist, якщо **StationName** не дорівнює '' і визначено **GalaxyMapBookmark** або
**SystemMapBookmark**, Waypoint Assist відкриє Galaxy Map або System Map і вибере
Station за закладкою. Позиція закладки у списку станцій **System Map** рахується зверху вниз і
починається з «1» для першої закладки. Значення 0 вимикає закладку.
Після прибуття на станцію SC Assist (який діє від імені Waypoint Assist) виведе корабель
із Supercruise і спробує здійснити docking. Після docking автоматично буде надіслано команди refuel і repair, а Trade виконається за потреби.

## Docking із System Colonisation Ship та Orbital Construction Site (лише Odyssey)
Дивіться *Docking зі станцією* вище. Єдина відмінність від звичайної станції полягає в тому, що єдина опція торгівлі — продати всі
товари кораблю. Див. розділ Trading.
<br>
_Примітка: Colonisation Ships і Construction Ships можна додати в закладки лише на рівні Galaxy Map._

## Docking із Fleet Carrier
Дивіться *Docking зі станцією* вище. Окрім Trading (Buy/Sell), Fleet Carriers мають опцію Transfer (to/from) Fleet Carrier, яка використовує параметр **FleetCarrierTransfer**. Transfer намагатиметься перенести всі товари з корабля/Fleet Carrier, тож передавання з Fleet Carrier не надто корисне.
<br>
_Примітка: здається, існує помилка, яка іноді не дозволяє додати Fleet Carrier у закладки System Map. Якщо так сталося, усе ще можна додати FC у закладки через Navigation Panel. Після додавання закладки вона стане доступною через System Map._

## Trading
Списки **SellCommodities** та **BuyCommodities** пов’язані з авто-торгівлею, і кожен waypoint має обидва списки; будь-який або обидва можуть бути порожніми. Якщо будь-який зі списків не порожній, виконувач торгівлі активується, відкриває Commodities Screen і виконує Selling, а потім Buying для кожного зазначеного товару, якщо його можна продати. Товари обробляються в указаному порядку, тому важливі позиції розміщуйте першими. Також є опція оновлювати кількість товарів під час купівлі та продажу.

Окрім списків **SellCommodities** та **BuyCommodities**, визначених для кожного waypoint, існує **GlobalShoppingList**, який є списком **BuyCommodities**, спільним для всіх waypoint. Це товари, які купуватимуться на кожному waypoint, якщо вони доступні **після** оброблення **BuyCommodities** для waypoint. Також є опція оновлювати кількість товарів під час купівлі та продажу.

# Поширені дії
Коротка довідка щодо типових сценаріїв:
### Подорож до далекої системи
* Введіть дані системи, залиште дані станції порожніми.
### Подорож до Station
* Введіть дані системи та станції, залиште дані товарів порожніми. Для подорожі в межах поточної системи залиште дані системи порожніми.
### Торгівля між станціями та/або Fleet Carrier
* Введіть (за потреби) дані системи та станції.
* Заповніть списки Buy/Sell.
### Transfer до/з Fleet Carrier
* Введіть (за потреби) дані системи та станції.
* Додайте товар «All» із кількістю «0» у списках Buy/Sell, щоб запустити Transfer.
### System Colonisation Ship / Orbital Construction Site
* Введіть (за потреби) дані системи та станції.
* Додайте товар «All» із кількістю «0» у списку Sell, щоб запустити продаж усіх товарів.

Повний приклад із примітками:
```py
{
    "GlobalShoppingList": {                 # Global shopping list. Спробує придбати ці товари на кожній станції
                                            #    перед купівлею товарів, визначених у waypoint. Не змінюйте цю назву.
        "BuyCommodities": {                 # Словник товарів для купівлі. Глобальних товарів для продажу немає.
            "Ceramic Composites": 14,       # Вкажіть назву товару та кількість
            "CMM Composite": 3029,
            "Insulating Membrane": 324
        },
        "UpdateCommodityCount": true,       # Оновлювати наведені вище кількості під час купівлі (не продажу).
        "Skip": true,                       # Ігнорується для shopping list
        "Completed": false                  # Ігнорується для shopping list
    },
    "1": {                                  # Ключ системи. Можна змінити на щось зручне, але він має бути унікальним.
        "SystemName": "Hillaunges",         # Назва цільової системи, яку використовують для пошуку системи в Galaxy Map. Якщо назва
                                            # системи порожня, вважається, що ціллю є поточна система.
        "StationName": "",                  # Назва пункту призначення (назва станції, FC тощо).
                                            #   Якщо порожня і закладка не встановлена, waypoint завершено після прибуття
                                            #   до системи.
        "GalaxyBookmarkType": "Sys",        # Тип закладки Galaxy Map. Може бути:
                                            #   'Fav' або '' — Favorites
                                            #   'Sys' — System
                                            #   'Bod' — Body
                                            #   'Sta' — Station
                                            #   'Set' — Settlement
                                            # Примітка: System Colonisation Ships додаються в закладки на рівні Gal Map, тож тут буде
                                            #   'Sta'.
        "GalaxyBookmarkNumber": 6,          # Індекс закладки в межах зазначеного типу.
                                            #   Встановіть 0 або -1, якщо закладки не використовуються.
        "SystemBookmarkType": "Fav",        # Тип закладки System Map. Може бути:
                                            #   'Fav' або '' — Favorites
                                            #   'Bod' — Body
                                            #   'Sta' — Station
                                            #   'Set' — Settlement
                                            #   'Nav' — особливий випадок, який використовує Navigation Panel (Panel #1) для
                                            #      вибору закладки.
                                            #      Переважно для цілей системи, що не відображаються в system map,
                                            #      наприклад Mega Ships.
                                            #      Зверніть увагу, що список Nav Panel дуже змінний залежно від того, що є в системі
                                            #      і де ви виходите в систему, тому спершу відфільтруйте Nav Panel. Використовуйте
                                            #      обережно.
                                            #   Примітка: System Colonisation Ships можна додати в закладки лише на рівні Gal Map,
                                            #       тож це не застосовується до Col Ships.
        "SystemBookmarkNumber": 1,          # Індекс закладки в межах зазначеного типу.
                                            #   Встановіть 0 або -1, якщо закладки не використовуються.
        "SellCommodities": {},              # Словник товарів для продажу. Такий самий формат, як у Global shopping list
                                            #   вище. Крім того, для Colonisation Ships і Fleet Carrier у режимі 'Transfer', оскільки потрібно передати всі товари, можна вказати '"All": 0'
                                            #   як товар для продажу, щоб запустити sell/transfer all.
        "BuyCommodities": {},               # Словник товарів для купівлі. Такий самий формат, як у Global shopping list
                                            #   вище. Якщо ви визначите глобальний і waypoint shopping list, waypoint-список
                                            #   буде оброблено першим. Крім того, для Colonisation
                                            #   Ships і Fleet Carrier у режимі 'Transfer', оскільки потрібно передати всі товари,
                                            #   можна вказати '"All": 0' як товар для купівлі, щоб запустити
                                            #   transfer all.
        "UpdateCommodityCount": true,       # Оновлювати наведені вище кількості під час купівлі (не продажу). Кількості продажу
                                            #   ніколи не оновлюються.
        "FleetCarrierTransfer": false,      # Якщо ця «станція» є Fleet Carrier, дозволяє опцію TRANSFER замість
                                            #   BUY/SELL, встановіть False для купівлі/продажу, True для Transfer. Transfer за умовчанням
                                            #   переміщує все, що маєте.
        "Skip": true,                       # Пропустити цей waypoint. EDAP не змінює це значення, тож це зручний спосіб вимкнути
                                            #   waypoint без видалення.
        "Completed": false                  # Якщо false, обробити цей waypoint. Після завершення EDAP встановить True. Коли
                                            #   всі waypoints завершені, EDAP поверне False.
    },
    "2": {
        "SystemName": "Synuefe ZX-M b54-1",
        "StationName": "System Colonisation Ship",
        "GalaxyBookmarkType": "Sys",
        "GalaxyBookmarkNumber": 1,
        "SystemBookmarkType": "",
        "SystemBookmarkNumber": -1,
        "SellCommodities": {
            "ALL": 0
        },
        "BuyCommodities": {},
        "FleetCarrierTransfer": false,
        "UpdateCommodityCount": true,
        "Skip": false,
        "Completed": false
    },
    "rep": {
        "SystemName": "REPEAT",             # Назва системи REPEAT змушує повторювати waypoints.
                                            # Лише поле 'Skip' нижче використовується, щоб «вимкнути» повторення
                                            # без видалення рядка.
        "StationName": "",
        "GalaxyBookmarkType": "",
        "GalaxyBookmarkNumber": -1,
        "SystemBookmarkType": "",
        "SystemBookmarkNumber": -1,
        "SellCommodities": {},
        "BuyCommodities": {},
        "FleetCarrierTransfer": false,
        "UpdateCommodityCount": false,
        "Skip": false,                      # Skip (вимикає) REPEAT.
        "Completed": false
    }
}
```

