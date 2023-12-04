# Avito Prcie Bot
**Avito Prcie Bot** – это бот [Telegram](https://telegram.org/) для сайта [Авито](https://www.avito.ru/), помогающий администрировать стоимость краткосрочно арендуемых помещений.

## Порядок установки и использования
1. Загрузить последний релиз. Распаковать.
2. Установить Python версии не старше 3.10.
3. В среду исполнения установить следующие пакеты: [dublib](https://github.com/DUB1401/dublib), [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI?ysclid=loq3f2bmuz181940716), [APScheduler](https://github.com/agronholm/apscheduler).
```
pip install git+https://github.com/DUB1401/dublib
pip install pyTelegramBotAPI
pip install APScheduler
```
Либо установить сразу все пакеты при помощи следующей команды, выполненной из директории скрипта.
```
pip install -r requirements.txt
```
4. Настроить используемого бота путём добавления в него списка команд из файла _Commands.txt_.
5. Настроить скрипт путём редактирования _Settings.json_.
6. Открыть директорию со скриптом в терминале. Можно использовать метод `cd` и прописать путь к папке, либо запустить терминал из проводника.
7. Указать для выполнения главный файл скрипта `main.py`, перейти в Telegram, отправить в чат с ботом команду `/start` и следовать дальнейшим инструкциям.
8. Для автоматического запуска службы рекомендуется провести инициализацию скрипта через [systemd](https://github.com/systemd/systemd) (пример [здесь](https://github.com/DUB1401/AvitoPriceBot/tree/main/systemd)) на Linux или путём добавления его в автозагрузку на Windows.

# Основные команды
Под основными командами понимаются конструкции, которые сам бот Telegram интерпретирует как команды. Они всегда начинаются с символа косой черты.
___
```
/flats
```
Выводит список заданных идентификаторов объявлений.
___
```
/help
```
Выводит описание доступных команд.
___
```
/jobs
```
Выводит список установленных работ.
___
```
/list
```
Выводит список подключённых профилей Авито.
___
```
/register
```
Запускает процедуру добавления нового профиля Авито.
___
```
/start
```
Инициализирует работу бота и запускает процесс авторизации.
___
```
/tasks
```
Выводит список запланированных задач.

# Функциональные команды
Под функциональными командами понимаются сообщения боту Telegram, имеющие особый синтаксис и порядок аргументов. Данные команды нечувствительны к регистру, все аргументы являются обязательными.
___
```
calendar [ACCOUNT*] [ITEM_ID*] [PRICE*] [EXTRA_PRICE*] [DAYS*]
```
Изменяет свойства ренты для выбранных дней недели текущего месяца.

**Описание позиций:**
* **ACCOUNT** – идентификатор профиля, использующегося для выполнения операции.
	* Аргумент – строка, не содержащая пробелов.
* **ITEM_ID** – ID объявления (можно получить из URL) или строковый идентификатор.
	* Аргумент – целое положительное число или строка, не содержащая пробелов и установленная при помощи основной команды `newflat`.
* **PRICE** – стоимость ренты или дельта для вычисления оной.
	* Аргумент – целое положительное число либо целое положительное число со знаками `+` или `-` для вычисления новой стоимости в зависимости базовой.
* **EXTRA_PRICE** – дополнительная стоимость за одного гостя.
	* Аргумент – целое не отрицательное число.
* **DAYS** – список сокращённых названий дней недели или символ `*`.
	* Аргумент – строка без пробелов, содержащая сокращённые наименования дней недели через запятую (_пн, вт, ср, чт, пт, сб, вс_), или символ `*`, указывающий на то, что необходимо произвести действия для всех дней текущего месяца.
___
```
dayprice [ACCOUNT*] [ITEM_ID*] [PRICE*] [EXTRA_PRICE*] [DATE*]
```
Изменяет свойства ренты для определённой даты.

**Описание позиций:**
* **ACCOUNT** – идентификатор профиля, использующегося для выполнения операции.
	* Аргумент – строка, не содержащая пробелов.
* **ITEM_ID** – ID объявления (можно получить из URL) или строковый идентификатор.
	* Аргумент – целое положительное число или строка, не содержащая пробелов и установленная при помощи основной команды `newflat`.
* **PRICE** – стоимость ренты или дельта для вычисления оной.
	* Аргумент – целое положительное число либо целое положительное число со знаками `+` или `-` для вычисления новой стоимости в зависимости базовой.
* **EXTRA_PRICE** – дополнительная стоимость за одного гостя.
	* Аргумент – целое не отрицательное число.
* **DATE** – дата, для которой изменяются свойства.
	* Аргумент – строка, описывающая дату в формате _DD.MM.YYYY_.
___
```
delflat [FLAT_NAME*]
```
Удаляет идентификатор объявления.

**Описание позиций:**
* **FLAT_NAME** – идентификатор объявления.
	* Аргумент – строка, не содержащая пробелов.
___
```
deljob [JOB_ID*]
```
Удаляет работу.

**Описание позиций:**
* **JOB_ID** – идентификатор работы.
	* Аргумент – целое положительное число.
___
```
deltask [TASK_ID*]
```
Удаляет задачу.

**Описание позиций:**
* **TASK_ID** – идентификатор задачи.
	* Аргумент – целое положительное число.
___
```
newflat [ITEM_ID*] [FLAT_NAME*]
```
Создаёт идентификатор объявления, который можно использовать в командах вместо ID.

**Описание позиций:**
* **ITEM_ID** – ID объявления (можно получить из URL) или строковый идентификатор.
	* Аргумент – целое положительное число или строка, не содержащая пробелов и установленная при помощи основной команды `newflat`.
* **FLAT_NAME** – идентификатор объявления.
	* Аргумент – строка, не содержащая пробелов.
___
```
newjob [ACCOUNT*] [ITEMS_ID*] [PRICE*] [EXTRA_PRICE*] [HOUR*]
```
Создаёт работу, модифицирующую свойства ренты в случае отстутвия брони до указанного времени.

**Описание позиций:**
* **ACCOUNT** – идентификатор профиля, использующегося для выполнения операции.
	* Аргумент – строка, не содержащая пробелов.
* **ITEM_ID** – ID объявления (можно получить из URL) или строковый идентификатор.
	* Аргумент – целое положительное число или строка, не содержащая пробелов и установленная при помощи основной команды `newflat` (можно указывать несколько объявлений через запятую).
* **PRICE** – стоимость ренты или дельта для вычисления оной.
	* Аргумент – целое положительное число либо целое положительное число со знаками `+` или `-` для вычисления новой стоимости в зависимости базовой.
* **EXTRA_PRICE** – дополнительная стоимость за одного гостя.
	* Аргумент – целое не отрицательное число.
* **HOUR** – час, в который запускается работа.
	* Аргумент – целое число из диапазона [0; 23].
___
```
newtask [ACCOUNT*] [ITEM_ID*] [PRICE*] [DAY*] [HOUR*] [MINUTE*]
```
Создаёт задачу с отложенным или регулярным выполнением, изменяющую базовую стоимость ренты.

**Описание позиций:**
* **ACCOUNT** – идентификатор профиля, использующегося для выполнения операции.
	* Аргумент – строка, не содержащая пробелов.
* **ITEM_ID** – ID объявления (можно получить из URL) или строковый идентификатор.
	* Аргумент – целое положительное число или строка, не содержащая пробелов и установленная при помощи основной команды `newflat`.
* **PRICE** – стоимость ренты или дельта для вычисления оной.
	* Аргумент – целое положительное число либо целое положительное число со знаками `+` или `-` для вычисления новой стоимости в зависимости базовой.
* **DAY** – день или дата, в которую запускается задача.
	* Аргумент – либо строка, описывающая дату в формате _DD.MM.YYYY_ (одноразовая задача), либо сокращённое наименование дня недели (_пн, вт, ср, чт, пт, сб, вс_).
* **HOUR** – час, в который запускается задача.
	* Аргумент – целое число из диапазона [0; 23].
* **MINUTE** – минута, в которую запускается задача.
	* Аргумент – целое число из диапазона [0; 59].
___
```
price [ACCOUNT*] [ITEM_ID*] [PRICE*]
```
Моментально задаёт новую базовую стоимость.

**Описание позиций:**
* **ACCOUNT** – идентификатор профиля, использующегося для выполнения операции.
	* Аргумент – строка, не содержащая пробелов.
* **ITEM_ID** – ID объявления (можно получить из URL) или строковый идентификатор.
	* Аргумент – целое положительное число или строка, не содержащая пробелов и установленная при помощи основной команды `newflat` (можно указывать несколько объявлений через запятую).
* **PRICE** – стоимость ренты или дельта для вычисления оной.
	* Аргумент – целое положительное число либо целое положительное число со знаками `+` или `-` для вычисления новой стоимости в зависимости базовой.
___
```
rename [OLD_ACCOUNT*] [NEW_ACCOUNT*]
```
Изменяет идентификатор профиля. Не путать с номером профиля!

**Описание позиций:**
* **OLD_ACCOUNT** – текущий идентификатор профиля.
	* Аргумент – строка, не содержащая пробелов.
* **NEW_ACCOUNT** – новый идентификатор профиля.
	* Аргумент – строка, не содержащая пробелов.
___
```
report [CHAT_ID*]
```
Задаёт ID чата для рассылки отчётов о выполнении отложенных задач.

**Описание позиций:**
* **CHAT_ID** – идентификатор чата. Можно узнать при помощи [Chat ID Bot](https://t.me/chat_id_echo_bot).
	* Аргумент – отрицательное целое число или ноль (отключает рассылку).
___
```
unregister [ACCOUNT*]
```
Удаляет профиль, а также связанные с ним задачи и работы.

**Описание позиций:**
* **ACCOUNT** – идентификатор профиля.
	* Аргумент – строка, не содержащая пробелов.

# Settings.json
```JSON
"token": ""
```
Сюда необходимо занести токен бота Telegram (можно получить у [BotFather](https://t.me/BotFather)).
___
```JSON
"bot-password": "1234"
```
Пароль для доступа к боту.
___
```JSON
"report-target": null
```
Указывает ID группы или канала для отправки отчётов о выполнении отложенных задач.
___
```JSON
"timezone": "Europe/Moscow"
```
Указывает часовой пояс для планировщика задач.
___
```JSON
"use-supervisor": true
```
Если включено, то для каждого добавленного профиля Авито будет создан поток-надзиратель, следящий за стабильным обновлением токенов доступа. Повышает стабильность работы скрипта, но незначительно увеличивает нагрузку на сервер.
___
```JSON
"recycling-id": true
```
Переключает режим генерации ID новых задач. Если отключить, ID будут постоянно увеличиваться, игнорируя освободившиеся номера.
___
```JSON
"delay": 1
```
Задаёт интервал в секундах между последовательными запросами к API Авито.

_Copyright © DUB1401. 2023._
