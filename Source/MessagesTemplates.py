from Source.Functions import EscapeCharacters
from time import sleep

import telebot
import enum

# Типы очередей сообщений.
class QueueTypes(enum.Enum):
	
	#---> Статические свойства.
	#==========================================================================================#
	# Профили пользователей.
	Profiles = "profiles"
	# Задачи.
	Tasks = "tasks"
	# Квартиры.
	Flats = "flats"
	# Работы.
	Jobs = "jobs"

# Шаблоны сообщений.
class MessagesTemplates:
	
	# Строит список описаний работ.
	def __BuildJobsDescriptions(self, Jobs: list) -> list[str]:
		# Описания работ.
		Descriptions = list()
		
		# Для каждой работы.
		for Job in Jobs:
			# Конверитрование цены в строку.
			Price = str(Job["price"])
			# Если используется полодительная дельта, добавить плюс.
			if Job["price"] > 0 and Job["delta"] == True: Price = "+" + Price
			# Сгенерировать описание пользователя.
			Bufer = "Идентификатор: " + str(Job["id"]) + "\n"
			Bufer += "Номер профиля: _*" + str(Job["profile"]) + "*_\n"
			if Job["flat"]!= None: Bufer += "Идентификатор объявления: _*" + EscapeCharacters(Job["flat"]) + "*_\n"
			Bufer += "ID объявления: " + str(Job["item-id"]) + "\n"
			Bufer += "Стоимость: " + EscapeCharacters(Price) + "\n"
			Bufer += "Доплата за гостя: " + str(Job["extra-price"]) + "\n"
			Bufer += "Время проверки: _" + EscapeCharacters(str(Job["hour"]).rjust(2, '0') + ":00") + "_\n"
			# Сохранение буфера.
			Descriptions.append(Bufer)
		
		return Descriptions
	
	# Строит список описаний квартир.
	def __BuildFlatsDescriptions(self, Flats: dict) -> list[str]:
		# Описания работ.
		Descriptions = list()
		
		# Для каждой работы.
		for FlatName in Flats.keys():
			# Сгенерировать описание пользователя.
			Bufer = "Имя: _*" + EscapeCharacters(FlatName) + "*_\n"
			Bufer += "Идентификатор: " + str(Flats[FlatName]) + "\n"
			# Сохранение буфера.
			Descriptions.append(Bufer)
		
		return Descriptions
	
	# Строит список описаний профилей.
	def __BuildProfilesDescriptions(self, UsersData: dict) -> list[str]:
		# Описания профилей.
		Descriptions = list()
	
		# Для каждого профиля.
		for UserID in UsersData.keys():
			# Сгенерировать описание пользователя.
			Bufer = "Идентификатор: _*" + EscapeCharacters(UserID) + "*_\n"
			Bufer += "Номер профиля: _*" + str(UsersData[UserID]["profile"]) + "*_\n"
			Bufer += "ID клиента: " + EscapeCharacters(UsersData[UserID]["client-id"]) + "\n"
			Bufer += "Секретный ключ клиента: " + EscapeCharacters(UsersData[UserID]["client-secret"]) + "\n"
			# Сохранение буфера.
			Descriptions.append(Bufer)
		
		return Descriptions

	# Строит список описаний задач.
	def __BuildTasksDescriptions(self, Tasks: dict) -> list[str]:
		# Описания задач.
		Descriptions = list()
	
		# Для каждой задачи.
		for TaskID in Tasks.keys():
			# Конвертирование стоимости в строку.
			Price = str(Tasks[TaskID]["method"]["price"])
		
			# Формирование стоимости.
			if Tasks[TaskID]["method"]["delta"] == True and Tasks[TaskID]["method"]["price"] > 0:
				# Добавление символа плюса.
				Price = "+" + Price
			
			# Буфер описания.
			Bufer = "Идентификатор: " + EscapeCharacters(TaskID) + "\n"
			Bufer += "Профиль Авито: " + Tasks[TaskID]["method"]["profile"] + "\n"
			if Tasks[TaskID]["method"]["flat"]!= None: Bufer += "Идентификатор объявления: _*" + Tasks[TaskID]["method"]["flat"] + "*_\n"
			Bufer += "ID объявления: " + str(Tasks[TaskID]["method"]["item-id"]) + "\n"
			Bufer += "Стоимость: " + EscapeCharacters(Price) + "\n"
		
			# Если тип триггера – cron.
			if Tasks[TaskID]["trigger"]["type"] == "cron":
				Bufer += "Условие: _каждый " + Tasks[TaskID]["trigger"]["day"] + " в " + str(Tasks[TaskID]["trigger"]["hour"]) + ":" + str(Tasks[TaskID]["trigger"]["minute"]) + "_\.\n"
			
			else:
				Bufer += "Условие: _" + EscapeCharacters(Tasks[TaskID]["trigger"]["day"]) + " в " + str(Tasks[TaskID]["trigger"]["hour"]) + ":" + str(Tasks[TaskID]["trigger"]["minute"]) + "_\.\n"
			
			# Сохранение буфера.
			Descriptions.append(Bufer)
		
		return Descriptions
	
	# Создаёт очередь сообщений-описаний.
	def __MakeQueue(self, Type: QueueTypes, Data: any, Header: str, ZeroItemsMessage: str) -> list[str]:
		# Список сообщений.
		Messages = list()
		# Список описаний.
		Descriptions = list()
		
		# Проверка типа данных.
		match Type:
			
			# Составление списка описаний квартир.
			case QueueTypes.Flats:
				Descriptions = self.__BuildFlatsDescriptions(Data) 
			
			# Составление списка описаний работ.
			case QueueTypes.Jobs:
				Descriptions = self.__BuildJobsDescriptions(Data)
				
			# Составление списка описаний профилей.
			case QueueTypes.Profiles:
				Descriptions = self.__BuildProfilesDescriptions(Data)
				
			# Составление списка описаний задач.
			case QueueTypes.Tasks:
				Descriptions = self.__BuildTasksDescriptions(Data) 
		
		# Если задач не запланировано.
		if len(Descriptions) == 0:
			# Создание стандартного сообщения.
			Messages.append(ZeroItemsMessage)

		# Если задачи помещаются в одно сообщение.
		elif len(Descriptions) <= self.__PagesFactor:
			# Создание сообщения с описанием задач.
			Messages.append(f"*{Header}*\n\n" + "\n".join(Descriptions))
		
		# Если задачи не помещаются в одно сообщение.
		elif len(Descriptions) > self.__PagesFactor:
			# Количество страниц.
			PagesCount = len(Descriptions) // self.__PagesFactor
			# Если страниц не хватает для отображения остатка, то добавить страницу.
			if len(Descriptions) % self.__PagesFactor > 0: PagesCount += 1
			# Буфер сообщения.
			Bufer = f"*{Header} \[1 / {PagesCount}\]*\n\n"
			# Индекс текущего сообщения на странице.
			CurrentIndex = 1
			# Текущая страница.
			Page = 1
			
			# Для каждого описания.
			for Index in range(0, len(Descriptions)):
				# Добавление описания в буфер.
				Bufer += Descriptions[Index] + "\n"
				
				# Если в сообщение добавлено достаточно описаний или описание последнее.
				if CurrentIndex == self.__PagesFactor or Index == len(Descriptions) - 1:
					# Создание сообщения со страницей описаний задач.
					Messages.append(Bufer)
					# Инкремент страницы.
					Page += 1
					# Обнуление буфера.
					Bufer = f"*{Header} \[{Page} / {PagesCount}\]*\n\n"
					# Обнуление индекса сообщения.
					CurrentIndex = 1
					
				# Инкремент текущего индекса.
				CurrentIndex += 1

		return Messages
	
	# Конструктор.
	def __init__(self, Bot: telebot.TeleBot):
		  
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Экземпляр бота.
		self.__Bot = Bot
		# Количество описаний в сообщении.
		self.__PagesFactor = 10
		
	# Отправляет сообщения: список квартир.
	def Flats(self, Flats: dict, ChatID: int):
		# Очередь сообщений описаний.
		Messages = self.__MakeQueue(
			Type = QueueTypes.Flats,
			Data = Flats,
			Header = "🏠 Список квартир",
			ZeroItemsMessage = "*🏠 Список квартир*\n\nВы не добавили ни одной квартиры\."
		)
					
		# Отправка каждого сообщения.
		for Message in Messages:
			# Отправка сообщения: необходимо авторизоваться.
			self.__Bot.send_message(ChatID, Message, parse_mode = "MarkdownV2")
			# Выжидание паузы.
			sleep(0.1)
		
	# Отправляет сообщения: список запланированных задач.
	def Jobs(self, Jobs: list, ChatID: int):
		# Очередь сообщений описаний.
		Messages = self.__MakeQueue(
			Type = QueueTypes.Jobs,
			Data = Jobs,
			Header = "⚒️ Список работ",
			ZeroItemsMessage = "*⚒️ Список работ*\n\nНичего не запланировано\."
		)
					
		# Отправка каждого сообщения.
		for Message in Messages:
			# Отправка сообщения: необходимо авторизоваться.
			self.__Bot.send_message(ChatID, Message, parse_mode = "MarkdownV2")
			# Выжидание паузы.
			sleep(0.1)
		
	# Отправляет сообщения: список профилей.
	def List(self, UserData: dict, ChatID: int):
		# Очередь сообщений описаний.
		Messages = self.__MakeQueue(
			Type = QueueTypes.Profiles,
			Data = UserData,
			Header = "👥 Профили",
			ZeroItemsMessage = "*⚠️ Предупреждение*\n\nВы не добавили ни одного профиля Авито\. Используйте команду /register и следуйте дальнейшим инструкциям\."
		)
					
		# Отправка каждого сообщения.
		for Message in Messages:
			# Отправка сообщения: необходимо авторизоваться.
			self.__Bot.send_message(ChatID, Message, parse_mode = "MarkdownV2")
			# Выжидание паузы.
			sleep(0.1)
		
	# Отправляет сообщения: список запланированных задач.
	def Tasks(self, Tasks: dict, ChatID: int):
		# Очередь сообщений описаний.
		Messages = self.__MakeQueue(
			Type = QueueTypes.Tasks,
			Data = Tasks,
			Header = "📝 Список задач",
			ZeroItemsMessage = "*📝 Список задач*\n\nНичего не запланировано\."
		)
					
		# Отправка каждого сообщения.
		for Message in Messages:
			# Отправка сообщения: необходимо авторизоваться.
			self.__Bot.send_message(ChatID, Message, parse_mode = "MarkdownV2")
			# Выжидание паузы.
			sleep(0.1)
	
	# Отправляет сообщение: необходимо авторизоваться.
	def UserAuthRequired(self, ChatID: int):
		# Отправка сообщения: необходимо авторизоваться.
		self.__Bot.send_message(
			ChatID,
			"🔒 Для использования команд вам необходимо авторизоваться. Введите команду /start и пришлите мне пароль к серверу."
		)