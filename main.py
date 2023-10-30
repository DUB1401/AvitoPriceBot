#!/usr/bin/python

from dublib.Methods import Cls, CheckPythonMinimalVersion, MakeRootDirectories, ReadJSON
from Source.Functions import EscapeCharacters, ParseCommand, UserAuthRequired
from Source.BotManager import *
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

# Если токен не указан, выбросить исключение.
if type(Settings["token"]) != str or Settings["token"].strip() == "":
	raise Exception("Invalid Telegram bot token.")

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ БОТА <<<<< #
#==========================================================================================#

# Список команд.
COMMANDS = [
	"price",
	"rename",
	"newtask"
]

# Запись в лог сообщения: заголовок рабочей области.
logging.info("====== Working ======")
# Токен для работы определенного бота телегамм.
Bot = telebot.TeleBot(Settings["token"])
# Менеджер данных бота.
BotData = BotManager(Settings)

#==========================================================================================#
# >>>>> ОБРАБОТКА ЗАПРОСОВ <<<<< #
#==========================================================================================#

# Обработка команды: help.
@Bot.message_handler(commands=["help"])
def ProcessCommandStart(Message: types.Message):
	# Сообщение-справка.
	HelpMessage = "*Справка*\n\n"
	# Добавление описания команд.
	HelpMessage += "*price* \[ACCOUNT\] \[ITEM_ID\] \[PRICE\]\n" + "Описание: _Задаёт новую стоимость\._\n\n"
	HelpMessage += "*rename* \[OLD_ACCOUNT\] \[NEW_ACCOUNT\]\n" + "Описание: _Изменяет идентификатор пользователя.\._\n\n" 
	HelpMessage += "*task* \[время\] \[идентификатор\] \[ID объявления\] \[действие\]\n" + "Описание: _Создаёт регулярную задачу\._\n\n" 

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
		UserAuthRequired(Bot, Message.chat.id)

# Обработка команды: list.
@Bot.message_handler(commands=["list"])
def ProcessCommandStart(Message: types.Message):
	
	# Проверка авторизации пользователя.
	if BotData.login(Message.from_user.id) == True:
		# Получение словаря пользователей.
		UsersData = BotData.getAvitoUsers()
		
		# Если нет добавленных пользователей.
		if len(UsersData.keys()) == 0:
			# Отправка сообщения: нет добавленных пользователей Авито.
			Bot.send_message(
				Message.chat.id,
				"Вы не добавили ни одного пользователя Авито. Используйте команду /register и следуйте дальнейшим инструкциям.",
				parse_mode = None,
				disable_web_page_preview = True
			)

		else:
			# Сообщение со списком.
			UsersMessage = "*Добавленные пользователи*\n\n"
			
			# Для каждого пользователя Авито.
			for User in UsersData.keys():
				# Сгенерировать описание пользователя.
				UsersMessage += "Идентификатор: " + EscapeCharacters(User) + "\n"
				UsersMessage += "Номер профиля: " + str(UsersData[User]["profile"]) + "\n"
				UsersMessage += "ID клиента: " + EscapeCharacters(UsersData[User]["client-id"]) + "\n"
				UsersMessage += "Секретный ключ клиента: " + EscapeCharacters(UsersData[User]["client-secret"]) + "\n\n"
				
			# Отправка сообщения: список добавленных пользователей Авито.
			Bot.send_message(
				Message.chat.id,
				UsersMessage.rstrip('\n'),
				parse_mode = "MarkdownV2",
				disable_web_page_preview = True
			)
	else:
		# Отправка сообщения: необходимо авторизоваться.
		UserAuthRequired(Bot, Message.chat.id)

# Обработка команды: register.
@Bot.message_handler(commands=["register"])
def ProcessCommandStart(Message: types.Message):
	
	# Проверка авторизации пользователя.
	if BotData.login(Message.from_user.id) == True:
		# Отправка сообщения: инструкция по регистрации клиента Авито.
		Bot.send_message(
			Message.chat.id,
			"*Добавление нового аккаунта*\n\nПришлите мне номер профиля Авито\. Узнать его можно на этой [странице](https://www.avito.ru/profile/basic)\.",
			parse_mode = "MarkdownV2",
			disable_web_page_preview = True
		)
		# Установка ожидаемого типа сообщения.
		BotData.setExpectedType(ExpectedMessageTypes.AvitoID)
	
	else:
		# Отправка сообщения: необходимо авторизоваться.
		UserAuthRequired(Bot, Message.chat.id)
		
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
					"Авторизация произведена успешно. Теперь вы можете использовать команды."
				)
				# Установка ожидаемого типа сообщения.
				BotData.setExpectedType(ExpectedMessageTypes.Undefined)
				
			else:
				# Отправка сообщения: авторизация не удалось.
				Bot.send_message(
					Message.chat.id,
					"Неверный пароль. Попробуйте ещё раз."
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
					"*Добавление нового аккаунта*\n\nПришлите мне ID клиента\. Узнать его можно на этой [странице](https://www.avito.ru/professionals/api) в разделе _Собственная разработка_\.",
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
				"*Добавление нового аккаунта*\n\nПришлите мне секретный ключ клиента\. Узнать его можно на этой [странице](https://www.avito.ru/professionals/api) в разделе _Собственная разработка_\.",
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
					"Новый пользователь Авито успешно добавлен. Вы можете получить список всех авторизованных пользователей при помощи команды /list.",
					parse_mode = None,
					disable_web_page_preview = True
				)
				
			else:
				# Отправка сообщения: инструкция по регистрации клиента Авито.
				Bot.send_message(
					Message.chat.id,
					"Не удалось добавить пользователя Авито. Пожалуйста, проверьте корректность введённых данных и повторите регистрацию снова.",
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
						"Мне не удалось найти такую команду. Полный список доступных методов можно посмотреть, отправив мне /help.",
						parse_mode = None,
						disable_web_page_preview = True
					)
					
				else:
					# Название команды.
					Command = CommandData[0]
					
					try:
						
						# Проверка соответствия команд.
						match Command:
							
							# Обработка команды: newtask.
							case "newtask":
								# Попытка выполнить команду.
								Result = BotData.cmd_newtask(CommandData[1], CommandData[2], CommandData[3], CommandData[4], (CommandData[5], CommandData[6]))
								
								# Если выполнение успешно.
								if Result == True:
									# Отправка сообщения: идентификатор успешно изменён.
									Bot.send_message(
										Message.chat.id,
										f"Задача успешно создана.",
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
					
					except FileExistsError as ExceptionData:
						# Запись в лог ошибки: неверный синтаксис команды.
						logging.error("Uncorrect command: \"" + " ".join(CommandData) + "\". Description: \"" + str(ExceptionData).rstrip('.') + "\".")
						# Отправка сообщения: неверный синтаксис.
						Bot.send_message(
							Message.chat.id,
							"Неверный синтаксис команды или ошибка в указанных параметрах.",
							parse_mode = None,
							disable_web_page_preview = True
						)

			else:
				# Отправка сообщения: необходимо авторизоваться.
				UserAuthRequired(Bot, Message.chat.id)		
			
# Запуск обработки запросов Telegram.
Bot.polling(none_stop = True)