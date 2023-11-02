from apscheduler.schedulers.background import BackgroundScheduler
from dublib.Methods import WriteJSON
from datetime import datetime

import logging

# Планировщик операций.
class Scheduler:
	
	# Конструктор.
	def __init__(self, TasksJSON: dict):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Планировщик задач.
		self.__Planner = BackgroundScheduler()
		# Словарь задач.
		self.__Tasks = TasksJSON
		
		# Запуск планировщика.
		self.__Planner.start()
	
	# Создаёт задачу с синтаксисом cron.
	def createCronTask(self, Task: any, Profile: str, ItemID: int, Price: int, IsDelta: bool, DayOfWeek: str, Time: tuple, ID: str | None = None) -> bool:
		# Состояние: успешна ли операция.
		IsSuccess = True
		# Словарь описания.
		Description = {
			"active": True,
			"method": {
				"profile": Profile,
				"item-id": ItemID,
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
		
		# Если задача новая.
		if ID == None:
			# Инкремент последнего ID.
			self.__Tasks["last-id"] += 1
			# Присвоение ID.
			ID = str(self.__Tasks["last-id"])
			
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
		# Перезапись файла.
		WriteJSON("Data/Tasks.json", self.__Tasks)

		return IsSuccess
	
	# Создаёт задачу с синтаксисом даты.
	def createDateTask(self, Task: any, Profile: str, ItemID: int, Price: int, IsDelta: bool, Date: tuple, Time: tuple, ID: str | None = None) -> bool:
		# Состояние: успешна ли операция.
		IsSuccess = True
		# Конвертирование даты.
		Date = Date.split('.')
		Date = (int(Date[0]), int(Date[1]), int(Date[2]))
		# Словарь описания.
		Description = {
			"active": True,
			"method": {
				"profile": Profile,
				"item-id": ItemID,
				"price": Price,
				"delta": IsDelta
			},
			"trigger": {
				"type": "date",
				"day": str(Date[0]) + "." + str(Date[1]) + "." + str(Date[2]),
				"hour": Time[0],
				"minute": Time[1],
				"repeat": True
			}
		}
		
		# Если задача новая.
		if ID == None:
			# Инкремент последнего ID.
			self.__Tasks["last-id"] += 1
			# Присвоение ID.
			ID = str(self.__Tasks["last-id"])
			
		# Остановка планировщика.
		self.__Planner.pause()
		# Создание задачи.
		self.__Planner.add_job(
			func = Task,
			trigger = "date",
			args = (Profile, ItemID, Price, IsDelta, ID),
			id = ID,
			run_date = datetime(Date[0], Date[1], Date[2], int(Time[0]), int(Time[1]))
		)
		# Включение планировщика.
		self.__Planner.resume()
		# Запись описания задачи.
		self.__Tasks["tasks"][ID] = Description
		# Перезапись файла.
		WriteJSON("Data/Tasks.json", self.__Tasks)

		return IsSuccess

	# Возвращает словарь задач.
	def getTasks(self) -> dict:
		return self.__Tasks["tasks"]

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