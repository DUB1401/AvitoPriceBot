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

# Шаблоны сообщений.
class MessagesTemplates:
	
	# Строит список описаний профилей.
	def __BuildProfilesDescriptions(self, UsersData: dict) -> list[str]:
		# Описания профилей.
		Descriptions = list()
	
		# Для каждого профиля.
		for UserID in UsersData.keys():
			# Сгенерировать описание пользователя.
			Bufer = "Идентификатор: " + EscapeCharacters(UserID) + "\n"
			Bufer += "Номер профиля: " + str(UsersData[UserID]["profile"]) + "\n"
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
		# Получение форматированного списка описаний.
		Descriptions = self.__BuildTasksDescriptions(Data) if Type == QueueTypes.Tasks else self.__BuildProfilesDescriptions(Data)
		
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