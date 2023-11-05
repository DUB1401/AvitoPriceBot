from dublib.Methods import RemoveRecurringSubstrings
from Source.DateParser import DateParser
from calendar import Calendar
from datetime import datetime

# Возвращает список недель месяца.
def GetCurrentMonth() -> list[list[int]]:
	# Инициализация календаря.
	CalendarObject = Calendar()
	# Получение списка дней текущего месяца.
	Days = CalendarObject.monthdayscalendar(datetime.now().year, datetime.now().month)
	
	return Days

# Экранирует символы при использовании MarkdownV2 разметки.
def EscapeCharacters(Post: str) -> str:
	# Список экранируемых символов. _ * [ ] ( ) ~ ` > # + - = | { } . !
	CharactersList = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

	# Экранировать каждый символ из списка.
	for Character in CharactersList:
		Post = Post.replace(Character, "\\" + Character)

	return Post

# Парсит команду.
def ParseCommand(Text: str, CommandsList: list[str]) -> list[str] | None:
	# Удаление лишних пробелов.
	Text = RemoveRecurringSubstrings(Text, "  ")
	# Приведение к нижнему регистру.
	Text = Text.lower()
	# Разбитие по пробелам.
	CommandData = Text.split()
	# Состояние: найдена ли такая команда.
	IsDeterminated = False
	
	# Если длина списка параметров команды недостаточная.
	if len(CommandData) < 2:
		# Обнуление данных команды.
		CommandData = None
	
	else:
		
		# Для каждого возможного варианта команды.
		for Command in CommandsList:
			
			# Если название команды в списке определённых, то переключить состояние определения.
			if Command in CommandData:
				IsDeterminated = True
				
		# Если команда не определена, то обнулить её.
		if IsDeterminated == False:
			CommandData = None
		
	return CommandData

# Возвращает список дат, подходящих под фильтр дней недели.
def GetDates(DaysOfWeek: str) -> list[DateParser]:
	# Список дат.
	Dates = list()
	# Дни недели.
	DaysOfWeek = DaysOfWeek.split(',')
	# Календарный список.
	Weeks = GetCurrentMonth()
	# Названия дней недели.
	Declaration = {
		"пн": 1,	
		"вт": 2,	
		"ср": 3,	
		"чт": 4,	
		"пт": 5,	
		"сб": 6,	
		"вс": 7	
	}
	# Индексы выбранных дней недели.
	IntegerDaysOfWeek = list()
	
	# Для каждого дня.
	for Day in DaysOfWeek:
		# Сохранить индекс дня недели.
		IntegerDaysOfWeek.append(Declaration[Day])
		
	# Для каждой недели.
	for Week in Weeks:
		
		# Для каждого дня.
		for Index in range(0, len(Week)):
			
			# Если день недели выбран и принадлежит текущему месяцу.
			if Index + 1 in IntegerDaysOfWeek and Week[Index] != 0:
				# Составление даты.
				Date = str(Week[Index]) + "." + str(datetime.now().month) + "." + str(datetime.now().year)
				# Записать дату.
				Dates.append(DateParser(Date))
	
	return Dates