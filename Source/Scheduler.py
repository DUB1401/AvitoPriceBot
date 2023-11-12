from apscheduler.schedulers.background import BackgroundScheduler
from Source.DateParser import DateParser
from dublib.Methods import WriteJSON
from datetime import datetime
from pytz import timezone
from time import sleep

import logging

# Планировщик операций.
class Scheduler:
	
	# Генерирует ID задачи согласно настройкам.
	def __GenerateID(self, Type: str) -> str:
		# ID задачи.
		ID = None

		# Если запрещено повторное использование ID.
		if self.__Settings["recycling-id"] == False:
			# Инкремент последнего ID.
			ID = str(self.__Tasks[f"last-{Type}-id"] + 1)
			
		else:
			# Текущий ID.
			CurrentID = 1
			
			# Всегда.
			while True:
				# ID задач или работ. 
				ListID = self.__Tasks[f"{Type}s"].keys() if Type == "task" else self.getJobsID()
				
				# Если текущий ID не обнаружен в файле описания задач.
				if CurrentID not in ListID:
					# Задать текущий ID.
					ID = str(CurrentID)
					# Остановка цикла.
					break
				
				# Если достигнут последний ID.
				elif CurrentID > self.__Tasks[f"last-{Type}-id"]:
					# Инкремент последнего ID.
					ID = str(self.__Tasks[f"last-{Type}-id"] + 1)
					# Остановка цикла.
					break
				
				# Инкремент ID.
				CurrentID += 1
		
		return ID
	
	# Удаляет работу из описаний.
	def __RemoveJob(self, TargetID: int):
		# Копирование описаний работ.
		Jobs = self.__Tasks["jobs"].copy()
		
		# Для каждой работы.
		for Index in range(0, len(Jobs)):
			
			# Если найдена работа с нужным ID.
			if Jobs[Index]["id"] == TargetID:
				# Удалить работу.
				self.__Tasks["jobs"].pop(Index)
			
	# Сохраняет задачи в файл.
	def __Save(self):
		# Максимальный ID задачи.
		MaxTaskID = 0
		# Максимальный ID работы.
		MaxJobID = 0
		# Список ключей задач.
		TasksKeys = list(map(int, self.__Tasks["tasks"].keys()))
		# Список ID работ.
		JobsID = self.getJobsID()

		# Если есть задачи.
		if len(TasksKeys) > 0:
			# Поиск максимального ID.
			MaxTaskID = int(max(TasksKeys))
			
		# Если есть работы.
		if len(JobsID) > 0:
			# Поиск максимального ID.
			MaxJobID = int(max(JobsID))
			
		# Перезапись последнего ID задачи.
		self.__Tasks["last-task-id"] = MaxTaskID
		# Перезапись последнего ID работы.
		self.__Tasks["last-job-id"] = MaxJobID
		# Индекс повтора попытки сохранения.
		Retry = 0
		
		# Всегда.
		while Retry < 3:
			
			try:
				# Перезапись файла.
				WriteJSON("Data/Tasks.json", self.__Tasks)
				# Остановка цикла.
				break
				
			except Exception:
				# Запись в лог ошибки:
				logging.error("Unable to save \"Tasks.json\".")
				# Инкремент индекса повтора.
				Retry += 1
		
	# Поток-обработчик работ.
	def __Worker(self):
		# Создание часового пояса.
		Timezone = timezone(self.__Settings["timezone"])
		# Получение текущего часа.
		Hour = datetime.now(Timezone).hour
		
		# Для каждой работы.
		for Job in self.__Tasks["jobs"]:
			# Формирование даты.
			Date = DateParser(str(datetime.now(Timezone).date()).replace('-', '.'))

			# Если час совпадает и на дату нет брони.
			if Job["hour"] == Hour and self.__Users[Job["profile"]].checkBooking(Date, Job["profile"], Job["item-id"]) == False:
				
				# Изменить свойства для текущего дня.
				self.__Users[Job["profile"]].setCalendarDayProperties(
					ItemID = Job["item-id"],
					Date = Date,
					Price = Job["price"],
					IsDelta = Job["delta"],
					ExtraPrice = Job["extra-price"],
					Flat = Job["flat"]
				)
				# Выжидание интервала.
				sleep(self.__Settings["delay"])
	
	# Конструктор.
	def __init__(self, Settings: dict, TasksJSON: dict, Users: dict):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Планировщик задач.
		self.__Planner = BackgroundScheduler({"apscheduler.timezone": Settings["timezone"]})
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Словарь задач.
		self.__Tasks = TasksJSON.copy()
		# Пользователи.
		self.__Users = Users
		
		# Если заданы работы.
		if len(TasksJSON["jobs"]) > 0:
			# Создание задачи.
			self.__Planner.add_job(
				func = self.__Worker,
				trigger = "cron",
				id = "WORKER",
				hour = "*"
			)
			# Немедленный запуск.
			self.__Worker()
		
		# Запуск планировщика.
		self.__Planner.start()
	
	# Создаёт задачу с синтаксисом cron.
	def createCronTask(self, Task: any, Profile: str, ItemID: int, Price: int, IsDelta: bool, DayOfWeek: str, Time: tuple, ID: str | None = None, Flat: str | None = None):
		# Если задача новая, то сгенерировать ID.
		if ID == None: ID = self.__GenerateID("task")
		# Словарь описания.
		Description = {
			"active": True,
			"method": {
				"profile": Profile,
				"item-id": ItemID,
				"flat": Flat,
				"price": Price,
				"delta": IsDelta
			},
			"trigger": {
				"type": "cron",
				"day": DayOfWeek,
				"hour": Time[0],
				"minute": Time[1],
				"repeat": True
			}
		}
		
		# Остановка планировщика.
		self.__Planner.pause()
		# Создание задачи.
		self.__Planner.add_job(
			func = Task,
			trigger = "cron",
			args = (ItemID, Price),
			id = ID,
			day_of_week = DayOfWeek, 
			hour = Time[0], 
			minute = Time[1]
		)
		# Включение планировщика.
		self.__Planner.resume()
		# Запись описания задачи.
		self.__Tasks["tasks"][ID] = Description
		# Сохранение задач в файл.
		self.__Save()
		# Запись в лог сообщения: задача создана.
		logging.info(f"Task with ID {ID} initialized. Trigger type: \"cron\".")
		
	# Создаёт задачу с синтаксисом даты.
	def createDateTask(self, Task: any, Profile: str, ItemID: int, Price: int, IsDelta: bool, Date: tuple, Time: tuple, ID: str | None = None, Flat: str | None = None):
		# Если задача новая, то сгенерировать ID.
		if ID == None: ID = self.__GenerateID("task")
		# Конвертирование даты.
		Date = Date.split('.')
		Date = (int(Date[0]), int(Date[1]), int(Date[2]))
		# Словарь описания.
		Description = {
			"active": True,
			"method": {
				"profile": Profile,
				"item-id": ItemID,
				"flat": Flat,
				"price": Price,
				"delta": IsDelta
			},
			"trigger": {
				"type": "date",
				"day": str(Date[0]) + "." + str(Date[1]) + "." + str(Date[2]),
				"hour": int(Time[0]),
				"minute": int(Time[1]),
				"repeat": True
			}
		}
			
		# Остановка планировщика.
		self.__Planner.pause()
		# Создание задачи.
		self.__Planner.add_job(
			func = Task,
			trigger = "date",
			args = (Profile, ItemID, Price, IsDelta, ID, Description["method"]["flat"]),
			id = ID,
			run_date = datetime(Date[0], Date[1], Date[2], int(Time[0]), int(Time[1]))
		)
		# Включение планировщика.
		self.__Planner.resume()
		# Запись описания задачи.
		self.__Tasks["tasks"][ID] = Description
		# Сохранение задач в файл.
		self.__Save()
		# Запись в лог сообщения: задача создана.
		logging.info(f"Task with ID {ID} initialized. Trigger type: \"date\".")
		
	# Создаёт работу.
	def createJob(self, Profile: str, ItemID: int, Price: int, IsDelta: bool, ExtraPrice: int, Hour: int, Flat: str | None = None):
		# ID.
		ID = self.__GenerateID("job")
		# Описание работы.
		Description = {
			"id": int(ID),
			"profile": Profile,
			"item-id": ItemID,
			"flat": Flat,
			"price": Price,
			"delta": IsDelta,
			"extra-price": ExtraPrice,
			"hour": Hour
		}

		# Добавление работы в описание.
		self.__Tasks["jobs"].append(Description)
		# Сохранение файла.
		self.__Save()
		# Немедленный запуск.
		self.__Worker()

	# Возвращает список работ.
	def getJobs(self) -> list[dict]:
		return self.__Tasks["jobs"]
	
	# Возвращает список ID работ.
	def getJobsID(self) -> list[int]:
		# Список ID.
		ID = list()

		# Для каждой работы.
		for Job in self.__Tasks["jobs"]:
			# Записать ID.
			ID.append(Job["id"])
			
		return ID

	# Возвращает словарь задач.
	def getTasks(self) -> dict:
		return self.__Tasks["tasks"].copy()
	
	# Удаляет работу.
	def removeJob(self, JobID: int) -> bool:
		# Состояние: успешна ли операция.
		IsSuccess = True
		
		# Если задача существует.
		if JobID in self.getJobsID():
			# Удаление записи о работе.
			self.__RemoveJob(JobID)
			# Сохранение файла.
			self.__Save()
			# Запись в лог сообщения: задача удалена.
			logging.info(f"Job with ID {JobID} was removed.")
			
		else:
			# Переключение состояния.
			IsSuccess = False
			# Запись в лог ошибки: не удалось удалить задачу.
			logging.error(f"Unable to remove job with ID {JobID}.")
			
		return IsSuccess

	# Удаляет задачу.
	def removeTask(self, TaskID: str, OnlyJSON: bool = False) -> bool:
		# Состояние: успешна ли операция.
		IsSuccess = True
		
		# Если задача существует.
		if TaskID in self.__Tasks["tasks"].keys():
			
			# Если указано, удалить постоянную задачу.
			if OnlyJSON == False and self.__Planner.get_job(TaskID) != None:
				# Остановка планировщика.
				self.__Planner.pause()
				# Удаление задачи.
				self.__Planner.remove_job(TaskID)
				# Включение планировщика.
				self.__Planner.resume()
				
			# Удаление записи о задаче.
			del self.__Tasks["tasks"][TaskID]
			# Перезапись файла.
			WriteJSON("Data/Tasks.json", self.__Tasks)
			# Запись в лог сообщения: задача удалена.
			logging.info(f"Task with ID {TaskID} was removed.")
			
		else:
			# Переключение состояния.
			IsSuccess = False
			# Запись в лог ошибки: не удалось удалить задачу.
			logging.error(f"Unable to remove task with ID {TaskID}.")
			
		return IsSuccess