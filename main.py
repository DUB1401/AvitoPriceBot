#!/usr/bin/python

from dublib.Methods import Cls, CheckPythonMinimalVersion, MakeRootDirectories, ReadJSON
from Source.MessagesTemplates import MessagesTemplates
from Source.BotManager import *
from Source.Functions import *
from telebot import types

import datetime
import logging
import telebot
import time
import sys
import os

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

# Проверка поддержки используемой версии Python.
CheckPythonMinimalVersion(3, 10)
# Создание папок в корневой директории.
MakeRootDirectories(["Data", "Logs"])

#==========================================================================================#
# >>>>> НАСТРОЙКА ЛОГГИРОВАНИЯ <<<<< #
#==========================================================================================#

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(":", "-")
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO, format = "%(asctime)s %(levelname)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")
# Отключение части сообщений логов библиотеки requests.
logging.getLogger("requests").setLevel(logging.CRITICAL)
# Отключение части сообщений логов библиотеки urllib3.
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# Отключение части сообщений логов библиотеки apscheduler.
logging.getLogger("apscheduler").setLevel(logging.CRITICAL)

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Запись в лог сообщения: заголовок подготовки скрипта к работе.
logging.info("====== Preparing to starting ======")
# Запись в лог используемой версии Python.
logging.info("Starting with Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro) + " on " + str(sys.platform) + ".")
# Расположении папки установки веб-драйвера в директории скрипта.
os.environ["WDM_LOCAL"] = "1"
# Отключение логов WebDriver.
os.environ["WDM_LOG"] = str(logging.NOTSET)
# Очистка консоли.
Cls()
# Чтение настроек.
Settings = ReadJSON("Settings.json")
# Запись в лог сообщения: используемый часовой пояс.
logging.info("Timezone: \"" + Settings["timezone"] + "\".")

# Если токен не указан, выбросить исключение.
if type(Settings["token"]) != str or Settings["token"].strip() == "":
	raise Exception("Invalid Telegram bot token.")

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ БОТА <<<<< #
#==========================================================================================#

# Список команд.
COMMANDS = [
	"deltask",
	"newtask",
	"price",
	"rename",
	"unregister"
]

# Запись в лог сообщения: заголовок рабочей области.
logging.info("====== Working ======")
# Токен для работы определенного бота телегамм.
Bot = telebot.TeleBot(Settings["token"])
# Менеджер данных бота.
BotData = BotManager(Settings)
# Контейнер сообщений.
Messages = MessagesTemplates(Bot)

#==========================================================================================#
# >>>>> ОБРАБОТКА ЗАПРОСОВ <<<<< #
#==========================================================================================#

# Обработка команды: help.
@Bot.message_handler(commands=["help"])
def ProcessCommandStart(Message: types.Message):
	# Сообщение-справка.
	HelpMessage = "*📗 Справка*\n\n"
	# Добавление описания команд.
	HelpMessage += "*deltask* \[TASK\_ID\]\n" + "Описание: _Удаляет задачу\._\n\n" 
	HelpMessage += "*newtask* \[ACCOUNT\] \[ITEM\_ID\] \[PRICE\] \[DAY\]\ \[HOUR\]\ \[MINUTE\]\n" + "Описание: _Создаёт задачу с отложенным или регулярным выполнением\._\n\n" 
	HelpMessage += "*price* \[ACCOUNT\] \[ITEM\_ID\] \[PRICE\]\n" + "Описание: _Моментально задаёт новую стоимость\._\n\n"
	HelpMessage += "*rename* \[OLD\_ACCOUNT\] \[NEW\_ACCOUNT\]\n" + "Описание: _Изменяет идентификатор пользователя\._\n\n" 
	HelpMessage += "*unregister* \[ACCOUNT\]\n" + "Описание: _Удаляет профиль\._\n\n" 
	
	# Проверка авторизации пользователя.
	if BotData.login(Message.from_user.id) == True:
		# Отправка сообщения: инструкция по регистрации клиента Авито.
		Bot.send_message(
			Message.chat.id,
			HelpMessage,
			parse_mode = "MarkdownV2",
			disable_web_page_preview = True
		)
	
	else:
		# Отправка сообщения: необходимо авторизоваться.
		Messages.UserAuthRequired(Message.chat.id)

# Обработка команды: list.
@Bot.message_handler(commands=["list"])
def ProcessCommandStart(Message: types.Message):
	
	# Проверка авторизации пользователя.
	if BotData.login(Message.from_user.id) == True:
		# Отправка сообщения: список профилей.
		Messages.List(BotData.getAvitoUsers(), Message.chat.id)
			
	else:
		# Отправка сообщения: необходимо авторизоваться.
		Messages.UserAuthRequired(Message.chat.id)

# Обработка команды: register.
@Bot.message_handler(commands=["register"])
def ProcessCommandStart(Message: types.Message):
	
	# Проверка авторизации пользователя.
	if BotData.login(Message.from_user.id) == True:
		# Отправка сообщения: инструкция по регистрации клиента Авито.
		Bot.send_message(
			Message.chat.id,
			"*🗃️ Добавление нового профиля*\n\nПришлите мне номер профиля Авито\. Узнать его можно на этой [странице](https://www.avito.ru/profile/basic)\.",
			parse_mode = "MarkdownV2",
			disable_web_page_preview = True
		)
		# Установка ожидаемого типа сообщения.
		BotData.setExpectedType(ExpectedMessageTypes.AvitoID)
	
	else:
		# Отправка сообщения: необходимо авторизоваться.
		Messages.UserAuthRequired(Message.chat.id)
		
# Обработка команды: start.
@Bot.message_handler(commands=["start"])
def ProcessCommandStart(Message: types.Message):
	# Описание авторизации.
	AuthorizationDescription = "\n\n🔓 Доступ к командам разрешён\."
	
	# Вход в бота.
	if BotData.login(Message.from_user.id, None) == False:
		# Изменить описание входа.
		AuthorizationDescription = "\n\n🔒 Отправьте пароль для доступа к серверу\."
		# Установка ожидаемого типа сообщения.
		BotData.setExpectedType(ExpectedMessageTypes.BotPassword)
		
	# Отправка сообщения: приветствие.
	Bot.send_message(
		Message.chat.id,
		"Здравствуйте\. Я бот, помогающий управлять ценами на краткосрочно арендуемые помещения [Avito](https://www.avito.ru/)\." + AuthorizationDescription,
		parse_mode = "MarkdownV2",
		disable_web_page_preview = True
	)
	
# Обработка команды: tasks.
@Bot.message_handler(commands=["tasks"])
def ProcessCommandStart(Message: types.Message):

	# Проверка авторизации пользователя.
	if BotData.login(Message.from_user.id) == True:
		# Отправка сообщения: список запланированных задач.
		Messages.Tasks(BotData.scheduler().getTasks(), Message.chat.id)
	
	else:
		# Отправка сообщения: необходимо авторизоваться.
		Messages.UserAuthRequired(Message.chat.id)
	
# Обработка текстовых сообщений.
@Bot.message_handler(content_types=["text"])
def ProcessTextMessage(Message: types.Message):
	
	# Реагирование на сообщение по ожидаемому типу.
	match BotData.getExpectedType():
		
		# Авторизация пользователя в боте.
		case ExpectedMessageTypes.BotPassword:
			
			# Если авторизация успешная.
			if BotData.login(Message.from_user.id, Message.text) == True:
				# Отправка сообщения: успешная авторизация.
				Bot.send_message(
					Message.chat.id,
					"🔓 Авторизация произведена успешно. Теперь вы можете использовать команды."
				)
				# Установка ожидаемого типа сообщения.
				BotData.setExpectedType(ExpectedMessageTypes.Undefined)
				
			else:
				# Отправка сообщения: авторизация не удалось.
				Bot.send_message(
					Message.chat.id,
					"🔒 Неверный пароль. Попробуйте ещё раз."
				)
				
		# Установка ID аккаунта Авито.
		case ExpectedMessageTypes.AvitoID:
			# Добавление номера профиля для регистрации.
			Result = BotData.addAvitoUserProfileID(Message.text.strip().replace(' ', ''))
			
			# Если удалось добавить номер профиля.
			if Result == True:
				# Отправка сообщения: инструкция по регистрации клиента Авито.
				Bot.send_message(
					Message.chat.id,
					"*🗃️ Добавление нового профиля*\n\nПришлите мне ID клиента\. Узнать его можно на этой [странице](https://www.avito.ru/professionals/api) в разделе _Собственная разработка_\.",
					parse_mode = "MarkdownV2",
					disable_web_page_preview = True
				)
				# Установка ожидаемого типа сообщения.
				BotData.setExpectedType(ExpectedMessageTypes.ClientID)
				
			else:
				# Отправка сообщения: не удалось добавить номер профиля.
				Bot.send_message(
					Message.chat.id,
					"Номер профиля должен содержать только цифры\. Попробуйте ещё раз\.",
					parse_mode = "MarkdownV2",
					disable_web_page_preview = True
				)
			
		# Установка ID клиента.
		case ExpectedMessageTypes.ClientID:
			# Добавление номера профиля для регистрации.
			BotData.addAvitoUserClientID(Message.text.strip())
			# Отправка сообщения: инструкция по регистрации клиента Авито.
			Bot.send_message(
				Message.chat.id,
				"*🗃️ Добавление нового профиля*\n\nПришлите мне секретный ключ клиента\. Узнать его можно на этой [странице](https://www.avito.ru/professionals/api) в разделе _Собственная разработка_\.",
				parse_mode = "MarkdownV2",
				disable_web_page_preview = True
			)
			# Установка ожидаемого типа сообщения.
			BotData.setExpectedType(ExpectedMessageTypes.ClientSecret)
			
		# Установка секретного ключа клиента.
		case ExpectedMessageTypes.ClientSecret:
			# Добавление номера профиля для регистрации.
			BotData.addAvitoUserClientSecret(Message.text.strip())
			# Регистрация пользователя.
			Result = BotData.register()
			# Установка ожидаемого типа сообщения.
			BotData.setExpectedType(ExpectedMessageTypes.Undefined)
			
			# Если регистрация успешна.
			if Result == True:
				# Отправка сообщения: инструкция по регистрации клиента Авито.
				Bot.send_message(
					Message.chat.id,
					"*🗃️ Добавление нового профиля*\n\nНовый профиль Авито добавлен\. Вы можете получить список всех профилей при помощи команды /list\.",
					parse_mode = "MarkdownV2",
					disable_web_page_preview = True
				)
				
			else:
				# Отправка сообщения: инструкция по регистрации клиента Авито.
				Bot.send_message(
					Message.chat.id,
					"Не удалось добавить профиль Авито. Пожалуйста, проверьте корректность введённых данных и повторите операцию снова.",
					parse_mode = None,
					disable_web_page_preview = True
				)
		
		# Тип сообщения не определён.
		case ExpectedMessageTypes.Undefined:
			
			# Проверка авторизации пользователя.
			if BotData.login(Message.from_user.id) == True:
				# Попытка парсинга команды.
				CommandData = ParseCommand(Message.text.strip(), COMMANDS)
				
				# Если не удалось опознать команду.
				if CommandData == None:
					# Отправка сообщения: не удалось найти команду.
					Bot.send_message(
						Message.chat.id,
						"*❗ Ошибка*\n\nМне не удалось найти такую команду\. Полный список доступных методов можно посмотреть, отправив мне /help\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True
					)
					
				else:
					# Название команды.
					Command = CommandData[0]
					
					try:
						
						# Проверка соответствия команд.
						match Command:
							
							# Обработка команды: deltask.
							case "deltask":
								# Попытка выполнить команду.
								Result = BotData.cmd_deltask(CommandData[1])
								
								# Если выполнение успешно.
								if Result == True:
									# Отправка сообщения: задача удалена.
									Bot.send_message(
										Message.chat.id,
										f"Задача удалена.",
										parse_mode = None,
										disable_web_page_preview = True
									)
									
								else:
									# Отправка сообщения: не удалось удалить задачу.
									Bot.send_message(
										Message.chat.id,
										f"Не удалось удалить задачу. Проверьте корректность указанного идентификатора.",
										parse_mode = None,
										disable_web_page_preview = True
									)
							
							# Обработка команды: newtask.
							case "newtask":
								# Попытка выполнить команду.
								Result = BotData.cmd_newtask(CommandData[1], CommandData[2], CommandData[3], CommandData[4], (CommandData[5], CommandData[6]))
								
								# Если выполнение успешно.
								if Result == True:
									# Отправка сообщения: идентификатор успешно изменён.
									Bot.send_message(
										Message.chat.id,
										f"Задача создана.",
										parse_mode = None,
										disable_web_page_preview = True
									)
									
								else:
									# Отправка сообщения: не удалось изменить идентификатор.
									Bot.send_message(
										Message.chat.id,
										f"Не удалось создать задачу.",
										parse_mode = None,
										disable_web_page_preview = True
									)
							
							# Обработка команды: price.
							case "price":
								# Попытка выполнить команду.
								Result = BotData.cmd_price(CommandData[1], CommandData[2], CommandData[3])
								
								# Если выполнение успешно.
								if Result == True:
									# Отправка сообщения: идентификатор успешно изменён.
									Bot.send_message(
										Message.chat.id,
										f"Для объявления *{CommandData[2]}* задана новая стоимость\.",
										parse_mode = "MarkdownV2",
										disable_web_page_preview = True
									)
									
								else:
									# Отправка сообщения: не удалось изменить идентификатор.
									Bot.send_message(
										Message.chat.id,
										f"Не удалось изменить стоимость аренды в объявлении *{CommandData[2]}*\.",
										parse_mode = "MarkdownV2",
										disable_web_page_preview = True
									)
							
							# Обработка команды: rename.
							case "rename":
								# Попытка выполнить команду.
								Result = BotData.cmd_rename(CommandData[1], CommandData[2])
								
								# Если выполнение успешно.
								if Result == True:
									# Отправка сообщения: идентификатор успешно изменён.
									Bot.send_message(
										Message.chat.id,
										f"Идентификатор пользователя Авито успешно изменён\. Используйте теперь *{CommandData[2]}* для исполнения команд от имени этого аккаунта\.",
										parse_mode = "MarkdownV2",
										disable_web_page_preview = True
									)
									
								else:
									# Отправка сообщения: не удалось изменить идентификатор.
									Bot.send_message(
										Message.chat.id,
										f"Не удалось изменить идентификатор для пользователя *{CommandData[1]}*\.",
										parse_mode = "MarkdownV2",
										disable_web_page_preview = True
									)
									
							# Обработка команды: unregister.
							case "unregister":
								# Попытка выполнить команду.
								Result = BotData.cmd_unregister(CommandData[1])
								
								# Если выполнение успешно.
								if Result == True:
									# Отправка сообщения: идентификатор успешно изменён.
									Bot.send_message(
										Message.chat.id,
										f"Профиль *{CommandData[1]}* удалён\.\n\n*⚠️ Предупреждение*\n\nЗадачи\, созданные для этого профиля\, остаются активными\. Удалите их вручную или назначьте для другого профиля идентификатор *{CommandData[1]}*\.",
										parse_mode = "MarkdownV2",
										disable_web_page_preview = True
									)
									
								else:
									# Отправка сообщения: не удалось изменить идентификатор.
									Bot.send_message(
										Message.chat.id,
										f"Не удалось удалить профиль с идентификатором *{CommandData[1]}*\.",
										parse_mode = "MarkdownV2",
										disable_web_page_preview = True
									)
					
					except FileExistsError as ExceptionData:
						# Запись в лог ошибки: неверный синтаксис команды.
						logging.error("Uncorrect command: \"" + " ".join(CommandData) + "\". Description: \"" + str(ExceptionData).rstrip('.') + "\".")
						# Отправка сообщения: неверный синтаксис.
						Bot.send_message(
							Message.chat.id,
							"*❗ Ошибка*\n\nНеверный синтаксис команды или ошибка в указанных параметрах\.",
							parse_mode = "MarkdownV2",
							disable_web_page_preview = True
						)

			else:
				# Отправка сообщения: необходимо авторизоваться.
				Messages.UserAuthRequired(Message.chat.id)		

# Запуск обработки запросов Telegram.
Bot.polling(none_stop = True)