# Парсер даты.
class DateParser:
	
	# Интерпретирует строку как дату.
	def __InterpreteStringAsDate(self, String: str):
		
		# Если в строке две точки.
		if String.count('.') == 2:
			# Разбитие строки по точкам.
			DateProperties = String.split('.')
			# Свойство: начинается ли дата с года.
			IsYearFirst = False
			
			# Для каждого свойства даты.
			for Index in range(0, len(DateProperties)):
				# Очистка нулей слева от цифры.
				DateProperties[Index] = DateProperties[Index].lstrip('0')
			
			# Для каждого свойства даты.
			for DateInteger in DateProperties:
				
				# Если свойство не целочисленное.
				if DateInteger.isdigit() == False:
					# Выброс исключения.
					raise Exception("Uncorrect date string.")
				
			# Начинается ли дата с года.
			if len(DateProperties[0]) == 4:
				# Переключение режима парсинга строки.
				IsYearFirst = True
			
			# Если дата начинается с года.
			if IsYearFirst == True:
				# Парсинг даты.
				self.__Year = int(DateProperties[0])
				self.__Mounth = int(DateProperties[1])
				self.__Day = int(DateProperties[2])
				
			else:
				# Парсинг даты.
				self.__Year = int(DateProperties[2])
				self.__Mounth = int(DateProperties[1])
				self.__Day = int(DateProperties[0])
				
		else:
			# Выброс исключения.
			raise Exception("Uncorrect date string.")
	
	# Конструктор.
	def __init__(self, Date: str):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# День.
		self.__Day = None
		# Месяц.
		self.__Mounth = None
		# Год.
		self.__Year = None
		
		# Интерпретирование строки в дату.
		self.__InterpreteStringAsDate(Date)
		
	# Возвращает текстовый вариант даты.
	def date(self, Separator: str = ".", Alignment: bool = True, YearFirst: bool = False) -> str:
		# Возвращаемое значение.
		Value = None
		# Список свойств даты.
		DateProperties = list()
		
		# Если включено выравнивание.
		if Alignment == True:
			# Заполнение свойств.
			DateProperties.append(str(self.__Day).rjust(2, '0'))
			DateProperties.append(str(self.__Mounth).rjust(2, '0'))
			DateProperties.append(str(self.__Year))
			
		else:
			# Заполнение свойств.
			DateProperties.append(str(self.__Day))
			DateProperties.append(str(self.__Mounth))
			DateProperties.append(str(self.__Year))
		
		# Если дата должна начинаться с года.
		if YearFirst == True:
			# Формирование даты.
			Value = DateProperties[2] + Separator + DateProperties[1] + Separator + DateProperties[0]
			
		else:
			# Формирование даты.
			Value = DateProperties[0] + Separator + DateProperties[1] + Separator + DateProperties[2]
		
		return Value
		
	# Возвращает день.
	def day(self) -> int:
		return self.__Day
		
	# Возвращает номер месяца.
	def mounth(self) -> int:
		return self.__Mounth
	
	# Возвращает год.
	def year(self) -> int:
		return self.__Year
		