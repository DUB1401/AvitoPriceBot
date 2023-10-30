from apscheduler.schedulers.background import BackgroundScheduler
from dublib.Methods import WriteJSON

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
	def createCronTask(self, Task: any, Profile: str, ItemID: int, Price: int, IsDelta: bool, DayOfWeek: str, Time: tuple = (0, 0)) -> bool:
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
				"day-of-week": DayOfWeek,
				"hour": Time[0],
				"minute": Time[1],
				"repeat": True
			}
		}
		# Инкремент последнего ID.
		self.__Tasks["last-id"] += 1
		# Остановка планировщика.
		self.__Planner.pause()
		# Создание задачи.
		self.__Planner.add_job(
			func = Task,
			trigger = "cron",
			args = (ItemID, Price),
			id = str(self.__Tasks["last-id"]),
			day_of_week = DayOfWeek, 
			hour = Time[0], 
			minute = Time[1]
		)
		# Включение планировщика.
		self.__Planner.resume()
		# Запись описания задачи.
		self.__Tasks["tasks"][str(self.__Tasks["last-id"])] = Description
		# Перезапись файла.
		WriteJSON("Data/Tasks.json", self.__Tasks)

		return IsSuccess
