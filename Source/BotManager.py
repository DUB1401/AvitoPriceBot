from dublib.Methods import ReadJSON, RenameDictionaryKey, WriteJSON
from Source.DateParser import DateParser
from Source.Scheduler import Scheduler
from Source.Functions import GetDates
from Source.Avito import AvitoUser
from time import sleep

import logging
import telebot
import enum

# Типы ожидаемых сообщений.
class ExpectedMessageTypes(enum.Enum):
	
	#---> Статические свойства.
	#==========================================================================================#
	# Секретный ключ клиента.
	ClientSecret = "client-secret"
	# Пароль для доступа к функциям бота.
	BotPassword = "bot-password"
	# Неопределённое сообщение.
	Undefined = "undefined"
	# ID клиента.
	ClientID = "client-id"
	# ID аккаунта Авито.
	AvitoID = "avito-id"
	# Команда.
	Command = "command"

# Менеджер данных бота.
class BotManager:
	
	# Добавляет разрешённого пользователя.
	def __AddAllowedUser(self, UserID: int):
		# Чтение файла данных бота.
		Bufer = ReadJSON("Data/Bot.json")
		# Добавление ID пользователя в JSON файл и список.
		self.__AllowedUsers.append(UserID)
		Bufer["allowed-users"].append(UserID)
		# Сохранение данных бота.
		WriteJSON("Data/Bot.json", Bufer)
	
	# Создаёт задачу в планировщике.
	def __CreateTask(self, Bufer: dict, ID: str | None = None):
		
		# Проверка по типу триггера.
		match Bufer["trigger"]["type"]:
					
			# Если тип триггера задачи – cron.
			case "cron":
				
				# Установка задачи.
				self.__Planner.createCronTask(
					Task = self.__Users[Bufer["method"]["profile"]].setPrice if Bufer["method"]["delta"] == False else self.__Users[Bufer["method"]["profile"]].setDeltaPrice,
					Profile = Bufer["method"]["profile"],
					ItemID = Bufer["method"]["item-id"],
					Price = Bufer["method"]["price"],
					IsDelta = Bufer["method"]["delta"],
					DayOfWeek = Bufer["trigger"]["day"],
					Time = (Bufer["trigger"]["hour"], Bufer["trigger"]["minute"]),
					ID = ID,
					Flat = Bufer["method"]["flat"]
				)
				
			# Если тип триггера задачи – date.
			case "date":
				
				# Установка задачи.
				self.__Planner.createDateTask(
					Task = self.__StartOnceTask,
					Profile = Bufer["method"]["profile"],
					ItemID = Bufer["method"]["item-id"],
					Price = Bufer["method"]["price"],
					IsDelta = Bufer["method"]["delta"],
					Date = Bufer["trigger"]["day"],
					Time = (Bufer["trigger"]["hour"], Bufer["trigger"]["minute"]),
					ID = ID,
					Flat = Bufer["method"]["flat"]
				)
				
	# Возвращает список номеров профилей.
	def __GetProfilesID(self) -> list[int]:
		# Список номеров профилей.
		Profiles = list()
		
		# Для каждого профиля записать номер.
		for ProfileID in self.__UsersData["profiles"].keys():
			Profiles.append(self.__UsersData["profiles"][ProfileID]["profile"])
			
		return Profiles
			
	# Очищает буфер регистрации аккаунта Авито.
	def __InitializeAvitoRegister(self):
		# Установка стандартных полей.
		self.__AvitoUserBufer = {
			"profile": None,
			"client-id": None,
			"client-secret": None
		}
	
	# Загружает список разрешённых пользователей.
	def __LoadAllowedUsers(self):
		# Чтение файла данных бота.
		self.__AllowedUsers = ReadJSON("Data/Bot.json")["allowed-users"]
		
	# Загружает пользователей Авито.
	def __LoadAvitoUsers(self):
		# Чтение файла данных Авито.
		self.__UsersData = ReadJSON("Data/Avito.json")
		
		# Для каждого пользователя.
		for User in self.__UsersData["profiles"].keys():
			# Инициализация буфера данных пользователя.
			self.__AvitoUserBufer = {
				"profile": self.__UsersData["profiles"][User]["profile"],
				"client-id": self.__UsersData["profiles"][User]["client-id"],
				"client-secret": self.__UsersData["profiles"][User]["client-secret"]
			}
			# Инициализация пользователя.
			self.register(User)
			
	# Загружает сохранённые задачи.
	def __LoadTasks(self):
		# Чтение файла задач.
		Tasks = ReadJSON("Data/Tasks.json")
		# Инициализация планировщика.
		self.__Planner = Scheduler(self.__Settings, Tasks, self.__Users)
		# Запись в лог сообщения: количество загруженных задач.
		logging.info("Tasks count: " + str(len(Tasks["tasks"].keys())) + ".")
		
		# Для каждой задачи.
		for TaskID in Tasks["tasks"].keys():
			# Запись задачи в буфер.
			Bufer = Tasks["tasks"][TaskID]
			
			# Если задача активна.
			if Bufer["active"] == True:
				
				# Если пользователь существует.
				if Tasks["tasks"][TaskID]["method"]["profile"] in self.__UsersData["profiles"].keys():
					# Создать задачу.
					self.__CreateTask(Bufer, TaskID)
					
				else:
					# Переключение активности задачи.
					Tasks["tasks"][TaskID]["active"] = False
					# Сохранение в файл.
					WriteJSON("Data/Tasks.json", Tasks)
					# Запись в лог предупреждения: задача неактивна.
					logging.warning(f"Task with ID {TaskID} marked as inactive.")
					
			else:
				# Запись в лог сообщения: задача пропущена.
				logging.info(f"Task with ID {TaskID} inactive. Skipped.")
				
	# Возвращает ID объявления по идентификатору.
	def __ProcessFlatName(self, FlatName: str) -> str:
		# Оригинальный идентификатор.
		OriginName = None
		
		# Если для квартиры определён идентификатор.
		if FlatName in self.__UsersData["flats"].keys():
			# Запись названия.
			OriginName = FlatName
			# Присвоение номера профиля вместо идентификатора.
			FlatName = self.__UsersData["flats"][FlatName]
		
		return OriginName, FlatName
				
	# Удаляет связанные с профилем работы.
	def __RemoveConnectedJobs(self, ProfileID: str):
		# Список описаний работ.
		Jobs = self.__Planner.getJobs()
		# Список ID задач.
		JobsKeys = self.__Planner.getJobsID()
		
		# Для каждой задачи.
		for JobID in JobsKeys:

			# Если для задачи задан удаляемый профиль.
			if Jobs[JobID]["profile"] == ProfileID:
				# Удаление работы.
				self.cmd_deljob(JobID)

	# Удаляет связанные с профилем задачи.
	def __RemoveConnectedTasks(self, ProfileID: str):
		# Словарь описаний задач.
		Tasks = self.__Planner.getTasks()
		# Список ID задач.
		TasksKeys = list(Tasks.keys())
		
		# Для каждой задачи.
		for TaskID in TasksKeys:

			# Если для задачи задан удаляемый профиль.
			if Tasks[TaskID]["method"]["profile"] == ProfileID:
				# Удаление задачи.
				self.cmd_deltask(TaskID)

	# Выполняет задачу один раз.
	def __StartOnceTask(self, Profile: str, ItemID: str, Price: int, IsDelta: bool, ID: str, Flat: str | None = None):
		# Запуск задачи.
		self.__Users[Profile].setPrice(ItemID, Price, Flat) if IsDelta == False else self.__Users[Profile].setDeltaPrice(ItemID, Price, Flat)
		# Удаление задачи.
		self.__Planner.removeTask(ID, True)

	# Конструктор.
	def __init__(self, Settings: dict, Bot: telebot.TeleBot):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Текущий тип ожидаемого сообщения.
		self.__ExpectedType = ExpectedMessageTypes.Undefined
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Буфер регистрации пользователя Авито.
		self.__AvitoUserBufer = None
		# Список разрешённых пользователей.
		self.__AllowedUsers = list()
		# Словарь данных пользователей.
		self.__UsersData = dict()
		# Словарь пользователей.
		self.__Users = dict()
		# Планировщик.
		self.__Planner = None
		# Словарь дней недели.
		self.__Days = {
			"пн": "MON",	
			"вт": "TUE",	
			"ср": "WED",	
			"чт": "THU",	
			"пт": "FRI",	
			"сб": "SAT",	
			"вс": "SUN",	
		}
		# Экземпляр бота.
		self.__Bot = Bot
		
		# Загрузка разрешённых пользователей.
		self.__LoadAllowedUsers()
		# Чтение и инициализация сохранённых пользователей.
		self.__LoadAvitoUsers()
		# Загрузка задач.
		self.__LoadTasks()
		
	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	# Добавляет в буфер ID аккаунта Авито.
	def addAvitoUserProfileID(self, AccountID: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = True
		# Инициализация буфера.
		self.__InitializeAvitoRegister()
		
		# Если номер профиля является числом.
		if AccountID.isdigit():
			# Записать номер профиля.
			self.__AvitoUserBufer["profile"] = int(AccountID)
			
		else:
			# Переключение состояния успешности.
			IsSuccess = False
			
		return IsSuccess
	
	# Добавляет в буфер ID клиента Авито.
	def addAvitoUserClientID(self, ClientID: str):
		self.__AvitoUserBufer["client-id"] = ClientID
		
	# Добавляет в буфер секретный ключ клиента Авито.
	def addAvitoUserClientSecret(self, ClientSecret: str):
		self.__AvitoUserBufer["client-secret"] = ClientSecret
		
	# Возвращает словарь пользователей Авито.
	def getAvitoUsers(self) -> dict:
		return self.__UsersData["profiles"]

	# Возвращает тип ожидаемого сообщения.
	def getExpectedType(self) -> ExpectedMessageTypes:
		return self.__ExpectedType
	
	# Возвращает словарь квартир.
	def getFlats(self) -> dict:
		return self.__UsersData["flats"]
		
	# Регистрирует нового пользователя Авито.
	def register(self, UserID: str | None = None) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		# Попытка получения токена доступа.
		User = AvitoUser(self.__Settings, self.__AvitoUserBufer["profile"], self.__AvitoUserBufer["client-id"], self.__AvitoUserBufer["client-secret"], self.__Bot)
		
		# Если токен получен.
		if User.getAccessToken() != None:
			
			# Если пользователь новый.
			if UserID == None:
				
				# Если пользователь с таким идентификатором не существует.
				if int(self.__AvitoUserBufer["profile"]) not in self.__GetProfilesID():
					# Помещение пользователя в словарь.
					self.__Users[str(self.__AvitoUserBufer["profile"])] = User
					# Запись данных пользователя.
					self.__UsersData["profiles"][str(self.__AvitoUserBufer["profile"])] = self.__AvitoUserBufer
					# Сохранение данных пользователей.
					WriteJSON("Data/Avito.json", self.__UsersData)
					# Переключение состояния успешности.
					IsSuccess = True
					
				else:
					# Номер профиля.
					Profile = int(self.__AvitoUserBufer["profile"])
					# Запись в лог ошибки: пользователь с таким идентификатором уже существует.
					logging.error(f"Profile {Profile} already exists.")
				
			else:
				# Помещение пользователя в словарь.
				self.__Users[UserID] = User

		# Обнуление профиля.
		self.__AvitoUserBufer = None
		
		return IsSuccess
	
	# Вход в бота.
	def login(self, UserID: int, Password: str | None = None) -> bool:
		# Состояние: зарегестрирован ли пользователь.
		IsRegistered = False
		
		# Если пользователь разрешён.
		if Password == None and UserID in self.__AllowedUsers:
			# Активация бота для пользователя.
			IsRegistered = True
			
		# Если пароль для нового пользователя верен.
		elif Password == self.__Settings["bot-password"]:
			# Активация бота для пользователя.
			IsRegistered = True
			# Включение пользователя в реестр разрешённых.
			self.__AddAllowedUser(UserID)
			
		return IsRegistered
	
	# Возвращает список задач.
	def scheduler(self) -> Scheduler:
		return self.__Planner
		
	# Задаёт тип ожидаемого сообщения.
	def setExpectedType(self, Type: ExpectedMessageTypes):
		self.__ExpectedType = Type
	
	#==========================================================================================#
	# >>>>> КОМАНДЫ <<<<< #
	#==========================================================================================#

	# Задаёт свойства для дней недели в календаре текущего месяца.
	def cmd_calendar(self, UserID: str, ItemID: str, Price: str, ExtraPrice: str, DaysOfWeek: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		# Состояние: используется дельта.
		IsDelta = False
		# Обработка идентификатора квартиры.
		Origin, ItemID = self.__ProcessFlatName(ItemID)
		
		# Если присутствует знак, то включить режим изменения по дельте.
		if '+' in Price or '-' in Price:
			IsDelta = True

		try:
			# Преобразование цены в целочисленный тип.
			Price = int(Price)
			
		except Exception:
			# Обнуление цены.
			Price = None
			
		# Если такой пользователь не авторизован.
		if UserID not in self.__Users.keys():
			# Запись в лог ошибки: не удалось найти пользователя с указанным идентификатором.
			logging.error(f"Unable to find user with identificator: \"{UserID}\".")
			
		# Если цена указана в неверном формате.
		elif Price == None:
			# Запись в лог ошибки: не удалось найти пользователя с указанным идентификатором.
			logging.error(f"Uncorrect price.")
			
		else:
			# Список дат.
			Dates = GetDates(self.__Settings["timezone"], DaysOfWeek)
			
			# Для каждой даты.
			for Date in Dates:
				# Изменение свойств для даты.
				IsSuccess = self.__Users[UserID].setCalendarDayProperties(ItemID, Date, Price, IsDelta, ExtraPrice = int(ExtraPrice), Flat = Origin, Deferred = False)
				# Выжидание интервала.
				sleep(0.1)
				
				# Если не удалось.
				if IsSuccess == False:
					# Выброс исключения.
					raise Exception("Unable to change calendar day properties.")
		
		return IsSuccess

	# Задаёт свойства для определённого дня в календаре.
	def cmd_dayprice(self, UserID: str, ItemID: str, Price: str, ExtraPrice: str, Date: DateParser) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		# Состояние: используется дельта.
		IsDelta = False
		# Обработка идентификатора квартиры.
		Origin, ItemID = self.__ProcessFlatName(ItemID)
		
		# Если присутствует знак, то включить режим изменения по дельте.
		if '+' in Price or '-' in Price:
			IsDelta = True

		try:
			# Преобразование цены в целочисленный тип.
			Price = int(Price)
			
		except Exception:
			# Обнуление цены.
			Price = None
			
		# Если такой пользователь не авторизован.
		if UserID not in self.__Users.keys():
			# Запись в лог ошибки: не удалось найти пользователя с указанным идентификатором.
			logging.error(f"Unable to find user with identificator: \"{UserID}\".")
			
		# Если цена указана в неверном формате.
		elif Price == None:
			# Запись в лог ошибки: не удалось найти пользователя с указанным идентификатором.
			logging.error(f"Uncorrect price.")
			
		else:
			# Изменение свойств для даты.
			IsSuccess = self.__Users[UserID].setCalendarDayProperties(ItemID, Date, Price, IsDelta, ExtraPrice = int(ExtraPrice), Flat = Origin, Deferred = False)
		
		return IsSuccess

	# Удаляет идентификатор квартиры.
	def cmd_delflat(self, FlatName: str) -> bool:
		# Состояние: успешно ли создание.
		IsSuccess = True
		
		# Если указанный идентификатор не занят.
		if FlatName in self.__UsersData["flats"].keys():
			# Удаление записи.
			del self.__UsersData["flats"][FlatName]
			# Сохранение файла.
			WriteJSON("Data/Avito.json", self.__UsersData)
		
		else:
			# Переключение состояния.
			IsSuccess = False
			
		return IsSuccess

	# Удаляет работу.
	def cmd_deljob(self, JobID: str) -> bool:
		return self.__Planner.removeJob(int(JobID))

	# Удаляет задачу.
	def cmd_deltask(self, TaskID: str) -> bool:
		return self.__Planner.removeTask(TaskID)
	
	# Создаёт квартиру.
	def cmd_newflat(self, FlatID: str, FlatName: str) -> bool:
		# Состояние: успешно ли создание.
		IsSuccess = True
		
		# Если указанный идентификатор не занят.
		if FlatName not in self.__UsersData["flats"].keys():
			# Запись нового идентификатора объявления.
			self.__UsersData["flats"][FlatName] = int(FlatID)
			# Сохранение файла.
			WriteJSON("Data/Avito.json", self.__UsersData)
			
		else:
			# Переключение состояния.
			IsSuccess = False
			
		return IsSuccess
	
	# Создаёт работу.
	def cmd_newjob(self, Profile: str, ItemID: str, Price: str, ExtraPrice: str, Hour: str) -> int:
		# Количество ошибок.
		ErrorsCount = 0
		# Состояние: используется дельта.
		IsDelta = False
		# Список объявлений.
		Items = list()
		
		# Если объявления указаны через запятую.
		if ',' in ItemID:
			
			# Для каждого объявления
			for ItemBufer in ItemID.split(','):
				# Обработка идентификатора квартиры.
				OriginName, ItemIntID = self.__ProcessFlatName(ItemBufer)
				# Буфер описания.
				Bufer = {
					"item-id": int(ItemIntID),
					"flat": OriginName
				}
				# Сохранение квартиры.
				Items.append(Bufer)
			
		else:
			# Обработка идентификатора квартиры.
			OriginName, ItemID = self.__ProcessFlatName(ItemID)
			# Сохранение профиля.
			Items.append({
				"item-id": int(ItemID),
				"flat": OriginName
			})
		
		# Если присутствует знак, то включить режим изменения по дельте.
		if '+' in Price or '-' in Price:
			IsDelta = True
		
		# Для всех профилей.
		for CurrentItem in Items:
		
			try:
				# Создание работы.
				self.__Planner.createJob(Profile, CurrentItem["item-id"], int(Price), IsDelta, int(ExtraPrice), int(Hour), Flat = CurrentItem["flat"])
			
			except Exception as ExceptionData:
				# Запись в лог ошибки:
				logging.error("Unable to create job. Description: \"" + str(ExceptionData) + "\".")
				# Инкремент ошибок.
				ErrorsCount += 1
			
		return ErrorsCount
	
	# Создаёт задачу с синтаксисом cron.
	def cmd_newtask(self, Profile: str, ItemID: str, Price: str, Day: str, Time: tuple) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = True
		# Состояние: включён ли режим дельта-цены.
		IsDelta = False
		# Обработка идентификатора квартиры.
		OriginName, ItemID = self.__ProcessFlatName(ItemID)
		# Тип задачи.
		Type = "cron"
		
		# Если указана дата.
		if Day.count('.') == 2:
			# Инвертированиедаты.
			Day = ".".join(reversed(Day.split('.')))
			# Изменение типа задачи.
			Type = "date"
			
		else:
			# Перевод RU названия дня недели в EN.
			Day = self.__Days[Day.lower()]

		# Если указан знак, включить дельта-режим.
		if '+' in Price or '-' in Price:
			IsDelta = True
			
		# Словарь описания.
		Description = {
			"active": True,
			"method": {
				"profile": Profile,
				"item-id": ItemID,
				"flat": OriginName,
				"price": int(Price),
				"delta": IsDelta
			},
			"trigger": {
				"type": Type,
				"day": Day,
				"hour": Time[0],
				"minute": Time[1],
				"repeat": True if Type == "cron" else False
			}
		}
		# Создание задачи.
		self.__CreateTask(Description)	

		return IsSuccess

	# Изменяет стоимость аренды.
	def cmd_price(self, UserID: str, ItemID: str, Price: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		# Состояние: используется дельта.
		IsDelta = False
		# Обработка идентификатора квартиры.
		Origin, ItemID = self.__ProcessFlatName(ItemID)
		
		# Если присутствует знак, то включить режим изменения по дельте.
		if '+' in Price or '-' in Price:
			IsDelta = True

		try:
			# Преобразование цены в целочисленный тип.
			Price = int(Price)
			
		except Exception:
			# Обнуление цены.
			Price = None
			
		# Если такой пользователь не авторизован.
		if UserID not in self.__Users.keys():
			# Запись в лог ошибки: не удалось найти пользователя с указанным идентификатором.
			logging.error(f"Unable to find user with identificator: \"{UserID}\".")
			
		# Если цена указана в неверном формате.
		elif Price == None:
			# Запись в лог ошибки: не удалось найти пользователя с указанным идентификатором.
			logging.error(f"Uncorrect price.")
			
		else:
			# Изменение стоимости аренды.
			IsSuccess = self.__Users[UserID].setPrice(ItemID, Price, Deferred = False) if IsDelta == False else self.__Users[UserID].setDeltaPrice(ItemID, Price, Deferred = False)
		
		return IsSuccess

	# Изменяет идентификатор пользователя.
	def cmd_rename(self, OldID: str, NewID: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		
		# Если такой пользователь добавлен.
		if OldID in self.__UsersData["profiles"].keys():
			# Переименовать его ключ.
			self.__UsersData["profiles"] = RenameDictionaryKey(self.__UsersData["profiles"], OldID, NewID)
			self.__Users = RenameDictionaryKey(self.__Users.copy(), OldID, NewID)
			# Переключить состояние.
			IsSuccess = True
			# Сохранение данных.
			WriteJSON("Data/Avito.json", self.__UsersData)
			# Запись в лог сообщения: пользователь удалён.
			logging.info(f"Profile \"{OldID}\" renamed to \"{NewID}\".")
			
		return IsSuccess
	
	# Задаёт группу или канал для отчётов об отложенных работах.
	def cmd_report(self, Bot: telebot.TeleBot, ChatID: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = True
		
		# Если чат не сбрасывается.
		if ChatID != "0":
		
			try:
				# Отправка сообщения: не удалось добавить номер профиля.
				Bot.send_message(
					ChatID,
					"📢 *Отчёты*\n\nТеперь [AvitoPriceBot](https://github.com/DUB1401/AvitoPriceBot) будет присылать сюда отчёты о выполненных отложенных задачах\.",
					parse_mode = "MarkdownV2",
					disable_web_page_preview = True
				)
				# Запись ID чата.
				self.__Settings["report-target"] = int(ChatID)
				# Сохранение настроек.
				WriteJSON("Settings.json", self.__Settings)
		
			except Exception as ExceptionData:
				# Запись в лог ошибки: не удалось задать цель для отправки отчётов.
				logging.error(f"Unable to set reports chat ID: {ChatID}. Description: {ExceptionData}.")
				# Переключение состояния.
				IsSuccess = False
				
		else:
			# Обнуление ID чата.
			self.__Settings["report-target"] = None
			# Сохранение настроек.
			WriteJSON("Settings.json", self.__Settings)
		
		return IsSuccess
	
	# Удаляет пользователя.
	def cmd_unregister(self, UserID: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		
		# Если такой пользователь существует.
		if UserID in self.__UsersData["profiles"].keys():
			# Удаление данных пользователя.
			del self.__UsersData["profiles"][UserID]
			del self.__Users[UserID]
			# Переключить состояние.
			IsSuccess = True
			# Сохранение данных.
			WriteJSON("Data/Avito.json", self.__UsersData)
			# Запись в лог сообщения: пользователь удалён.
			logging.info(f"Profile \"{UserID}\" unregistered.")
			# Удаление связанных задач и работ.
			self.__RemoveConnectedTasks(UserID)
			self.__RemoveConnectedJobs(UserID)
		
		return IsSuccess