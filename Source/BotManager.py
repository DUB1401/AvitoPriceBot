from dublib.Methods import ReadJSON, RenameDictionaryKey, WriteJSON
from Source.Scheduler import Scheduler
from Source.Avito import AvitoUser

import logging
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
					ID = ID
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
					ID = ID
				)
	
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
		for User in self.__UsersData.keys():
			# Инициализация буфера данных пользователя.
			self.__AvitoUserBufer = {
				"profile": self.__UsersData[User]["profile"],
				"client-id": self.__UsersData[User]["client-id"],
				"client-secret": self.__UsersData[User]["client-secret"]
			}
			# Инициализация пользователя.
			self.register(User)
			
	# Загружает сохранённые задачи.
	def __LoadTasks(self):
		# Чтение файла задач.
		Tasks = ReadJSON("Data/Tasks.json")
		# Инициализация планировщика.
		self.__Planner = Scheduler(Tasks)
		# Запись в лог сообщения: количество загруженных задач.
		logging.info("Tasks count: " + str(len(Tasks["tasks"].keys())) + ".")
		
		# Для каждой задачи.
		for TaskID in Tasks["tasks"].keys():
			# Запись задачи в буфер.
			Bufer = Tasks["tasks"][TaskID]
			
			# Если задача активна, то загрузить её.
			if Bufer["active"] == True:
				self.__CreateTask(Bufer, TaskID)
		
	# Выполняет задачу один раз.
	def __StartOnceTask(self, Profile: str, ItemID: str, Price: int, IsDelta: bool, ID: str):
		# Запуск задачи.
		self.__Users[Profile].setPrice(ItemID, Price) if IsDelta == False else self.__Users[Profile].setDeltaPrice(ItemID, Price)
		# Удаление задачи.
		self.__Planner.removeTask(ID, True)

	# Конструктор.
	def __init__(self, Settings: dict):
		
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
		# Состояние: активен ли бот.
		self.__IsActive = False
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
		return self.__UsersData

	# Возвращает тип ожидаемого сообщения.
	def getExpectedType(self) -> ExpectedMessageTypes:
		return self.__ExpectedType
		
	# Регистрирует нового пользователя Авито.
	def register(self, UserID: str | None = None) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		# Попытка получения токена доступа.
		User = AvitoUser(self.__Settings, self.__AvitoUserBufer["profile"], self.__AvitoUserBufer["client-id"], self.__AvitoUserBufer["client-secret"])
		
		# Если токен получен.
		if User.getAccessToken() != None:
			# Переключение состояния успешности.
			IsSuccess = True
			
			# Если пользователь новый.
			if UserID == None:
				# Помещение пользователя в словарь.
				self.__Users[str(self.__AvitoUserBufer["profile"])] = User
				# Запись данных пользователя.
				self.__UsersData[str(self.__AvitoUserBufer["profile"])] = self.__AvitoUserBufer
				# Сохранение данных пользователей.
				WriteJSON("Data/Avito.json", self.__UsersData)
				
			else:
				# Помещение пользователя в словарь.
				self.__Users[UserID] = User

		# Обнуление профиля.
		self.__AvitoUserBufer = None
		
		return IsSuccess
	
	# Вход в бота.
	def login(self, UserID: int, Password: str | None = None) -> bool:
		
		# Если пользователь разрешён.
		if Password == None and UserID in self.__AllowedUsers:
			# Активация бота для пользователя.
			self.__IsActive = True
			
		# Если пароль для нового пользователя верен.
		elif Password == self.__Settings["bot-password"]:
			# Активация бота для пользователя.
			self.__IsActive = True
			# Включение пользователя в реестр разрешённых.
			self.__AddAllowedUser(UserID)
			
		return self.__IsActive
	
	# Возвращает список задач.
	def scheduler(self) -> Scheduler:
		return self.__Planner
		
	# Задаёт тип ожидаемого сообщения.
	def setExpectedType(self, Type: ExpectedMessageTypes):
		self.__ExpectedType = Type
	
	#==========================================================================================#
	# >>>>> КОМАНДЫ <<<<< #
	#==========================================================================================#

	# Удаляет задачу.
	def cmd_deltask(self, TaskID: str) -> bool:
		return self.__Planner.removeTask(TaskID)

	# Изменяет стоимость аренды.
	def cmd_price(self, UserID: str, ItemID: str, Price: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		# Состояние: используется дельта.
		IsDelta = False
		
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
			IsSuccess = self.__Users[UserID].setPrice(ItemID, Price) if IsDelta == False else self.__Users[UserID].setDeltaPrice(ItemID, Price)
		
		return IsSuccess

	# Изменяет идентификатор пользователя.
	def cmd_rename(self, OldID: str, NewID: str) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = False
		
		# Если такой пользователь добавлен.
		if OldID in self.__UsersData.keys():
			# Переименовать его ключ.
			self.__UsersData = RenameDictionaryKey(self.__UsersData.copy(), OldID, NewID)
			self.__Users = RenameDictionaryKey(self.__Users.copy(), OldID, NewID)
			# Переключить состояние.
			IsSuccess = True
			# Сохранение данных.
			WriteJSON("Data/Avito.json", self.__UsersData)
		
		return IsSuccess
	
	# Создаёт задачу с синтаксисом cron.
	def cmd_newtask(self, Profile: str, ItemID: str, Price: str, Day: str, Time: tuple) -> bool:
		# Состояние: успешна ли регистрация.
		IsSuccess = True
		# Состояние: включён ли режим дельта-цены.
		IsDelta = False
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