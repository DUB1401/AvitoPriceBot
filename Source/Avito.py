from Source.DateParser import DateParser
from threading import Thread
from time import sleep

import requests
import logging
import json

# Менеджер аккаунта Авито.
class AvitoUser:
	
	# Возвращает страницу со списком объявлений.
	def __GetItemsPage(self, Page: int, Count: int = 25) -> list[dict]:
		# Заголовки запроса.
		Headers = {
			"authorization": self.getAccessToken()
		}
		# Запрос данных объявления.
		Response = self.__Session.get(f"https://api.avito.ru/core/v1/items?page={Page}&per_page={Count}", headers = Headers)
		# Список объявлений на странице.
		Items = None
		
		# Если запрос не был успешным.
		if Response.status_code != 200:
			# Запись в лог ошибки: не удалось получить данные объявления.
			logging.error(f"Profile: {self.__ProfileID}. Unable to request items on page {Page}. Response code: " + str(Response.status_code) + ".")
			
		else:
			
			try:
				# Получение URL объявления.
				Items = dict(json.loads(Response.text))["resources"]
				
			except Exception as ExceptionData:
				# Запись в лог ошибки: не удалось преобразовать данные в JSON.
				logging.error(f"Profile: {self.__ProfileID}. Unable to convert items data on page {Page} to JSON. Description: \"" + str(ExceptionData).rstrip('.') + "\".")
				
		return Items
	
	# Получает токен для пользователя.
	def __RefreshAccessToken(self):
		# Параметры запроса.
		Params = {
			"grant_type": "client_credentials",
			"client_id": self.__ClientID,
			"client_secret": self.__ClientSecret
		}
		# Заголовки запроса.
		Headers = {
			"Content-Type": "application/x-www-form-urlencoded"
		}
		# Запрос нового токена доступа.
		Response = self.__Session.post("https://api.avito.ru/token/", headers = Headers, params = Params)
		
		# Проверка ответа.
		if Response.status_code == 200:
			# Интерпретация ответа в словарь.
			self.__AccessToken = dict(json.loads(Response.text))
			
			# Если запрос содержит ошибку.
			if "error" in self.__AccessToken.keys():
				# Запись в лог ошибки: не удалось обновить токен доступа.
				logging.error("Profile: {self.__ProfileID}. Unable to refresh access token. Description: \"" + self.__AccessToken["error_description"].rstrip('.') + "\".")
				# Обнуление токена доступа.
				self.__AccessToken = None
				
			else:
				# Запись в лог сообщения: токен обновлён.
				logging.info(f"Profile: {self.__ProfileID}. Token refreshed.")
		else:
			# Запись в лог ошибки: не удалось обновить токен доступа.
			logging.error(f"Profile: {self.__ProfileID}. Unable to refresh access token. Response code: " + str(Response.status_code) + ".")
			# Обнуление токена доступа.
			self.__AccessToken = None
			
	# Поток обновления токена.
	def __UpdaterThread(self):
		
		# Постоянно.
		while True:
			# Выжидание 23-ёх часов.
			sleep(float(23 * 60))
			# Обновление токен.
			self.__RefreshAccessToken()
			
	# Поток-надзиратель.
	def __SupervisorThread(self):
		
		# Постоянно.
		while True:
			# Выжидание 5-ти минут.
			sleep(5 * 60)

			# Если поток обновления токена остановлен.
			if self.__Updater.is_alive() == False:
				# Запись в лог предупреждения: поток обновления токена был остановлен.
				logging.warning(f"Profile: {self.__ProfileID}. Token updater thread was stopped.")
				# Реинициализация потока обновления токена.
				self.__Updater = Thread(target = self.__UpdaterThread, name = f"Profile {self.__ProfileID} supervisor thred.")
				# Запуск потока.
				self.__Updater.start()
		
	# Конструктор.
	def __init__(self, Settings: dict, Profile: int, ClientID: str, ClientSecret: str):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Номер профиля Авито.
		self.__ProfileID = Profile
		# Сессия запросов.
		self.__Session = requests.Session()
		# ID клиента.
		self.__ClientID = ClientID
		# Секретный ключ клиента.
		self.__ClientSecret = ClientSecret
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		#  Текущий токен.
		self.__AccessToken = None
		# Поток-надзиратель.
		self.__Supervisor = Thread(target = self.__SupervisorThread, name = f"Profile {Profile} updater thred.")
		# Поток обновления токена.
		self.__Updater = Thread(target = self.__UpdaterThread, name = f"Profile {Profile} supervisor thred.")
		
		# Получение токена доступа.
		self.__RefreshAccessToken()
		# Запуск потока обновления токена.
		self.__Updater.start()
		
		# Если указано настройками, запустить поток надзиратель.
		if Settings["use-supervisor"] == True:
			self.__Supervisor.start()
			
	# Проверяет, забронирована ли квартира на сегодня.
	def checkBooking(self, Date: DateParser, Profile: int | str, ItemID: int | str) -> bool:
		# Состояние: забронирована ли квартира.
		IsBooking = False
		# Преобразование даты в нужный формат.
		Date = Date.date("-", True, True)
		# Отправка запроса на получение броней.
		Response = self.__Session.get(f"https://api.avito.ru/realty/v1/accounts/{Profile}/items/{ItemID}/bookings?date_start={Date}&date_end={Date}&with_unpaid=true")
		
		# Проверка ответа.
		if Response.status_code != 200:
			# Запись в лог ошибки: не удалось изменить свойства.
			logging.error(f"Profile: {self.__ProfileID}. Unable to check bookings.")
			
		else:
			# Список броней.
			Bookings = dict(json.loads(Response.text))["bookings"]
			
			# Если брони есть.
			if len(Bookings) > 0:
				# Переключение состояния.
				IsBooking = True
		
			# Запись в лог сообщения: свойства даты изменены.
			logging.error(f"Profile: {self.__ProfileID}. Bookings: " + str(len(Bookings)) + ".")
		
		return IsBooking
		
	# Возвращает токен доступа.
	def getAccessToken(self) -> str:
		# Токен доступа.
		AccessToken = None
		
		# Если данные токена получены, то составить его.
		if self.__AccessToken != None:
			AccessToken = self.__AccessToken["token_type"] + " " + self.__AccessToken["access_token"]

		return AccessToken
	
	# Возвращает URL объявления.
	def getItemURL(self, ItemID: int | str) -> str | None:
		# Заголовки запроса.
		Headers = {
			"authorization": self.getAccessToken()
		}
		# Запрос данных объявления.
		Response = self.__Session.get(f"https://api.avito.ru/core/v1/accounts/{self.__ProfileID}/items/{ItemID}/", headers = Headers)
		# URL объявления.
		ItemURL = None
		
		# Если запрос не был успешным.
		if Response.status_code != 200:
			# Запись в лог ошибки: не удалось получить данные объявления.
			logging.error(f"Profile: {self.__ProfileID}. Unable to request item data. Response code: " + str(Response.status_code) + ".")
			
		else:
			
			try:
				# Получение URL объявления.
				ItemURL = dict(json.loads(Response.text))["url"]
				
			except Exception as ExceptionData:
				# Запись в лог ошибки: не удалось преобразовать данные в JSON.
				logging.error(f"Profile: {self.__ProfileID}. Unable to convert item data to JSON. Description: \"" + str(ExceptionData).rstrip('.') + "\".")
			
		
		return ItemURL
	
	# Возвращает список объявлений профиля.
	def getItemsList(self) -> list[dict] | None:
		# Список объявлений.
		Items = list()
		# Текущая страница.
		Page = 1
		
		# Пока не закончатся страницы.
		while Page != None:
			# Получение списка объявлений.
			Bufer = self.__GetItemsPage(Page)
			
			# Если буфер не нулевой.
			if Bufer != None:
				# Объединение списков объявлений.
				Items.extend(Bufer)
				
				# Если страница была последней.
				if len(Bufer) < 25:
					# Остановка запросов.
					Page = None
					
				else:
					# Выжидание интервала.
					sleep(self.__Settings["delay"])

			else:
				# Остановка запросов.
				Page = None
				# Запись в лог ошибки:
				logging.error(f"Profile: {self.__ProfileID}. Unable to request items list.")
				# Обнуление списка.
				Items = None
			
		return Items
	
	# Возвращает стоимость объявления.
	def getPrice(self, ItemID: str) -> int | None:
		# Получение URL объявления.
		ItemURL = self.getItemURL(ItemID)
		# Получение списка объявлений профиля.
		Items = self.getItemsList()
		# Стоимость.
		Price = None
		
		# Для каждого объявления.
		for Item in Items:
			
			# Если совпадает URL искомого объявления и текущего.
			if ItemURL == Item["url"]:
				# Сохранение стоимости.
				Price = Item["price"]
				
		try:
			# Преобразование цены в целочисленный тип.
			Price = int(Price)
			
		except Exception:
			# Обнуление стоимости.
			Price = None

		return Price
	
	# Задаёт свойства для конкретного дня.
	def setCalendarDayProperties(self, ItemID: str, Date: DateParser, Price: int, IsDelta: bool, Duration: int = 1, ExtraPrice: int = 0) -> bool:
		# Заголовки запроса.
		Headers = {
			"authorization": self.getAccessToken()
		}
		# Состояние: успешен ли запрос.
		IsSuccess = True
		# Конвертирование даты.
		StringDate = Date.date("-", True, True)
		# Опции запроса.
		Options = {
			"prices": [
				{
				"date_from": StringDate,
				"date_to": StringDate,
				"minimal_duration": int(Duration),
				"extra_guest_fee": int(ExtraPrice),
				"night_price": int(Price)
				}
			]	
		}
		
		# Если не используется дельта-сумма.
		if IsDelta == True:
			Options["prices"][0]["night_price"] = self.getPrice(ItemID) + int(Price)
		
		# Отправка запроса на изменение свойств.
		Response = self.__Session.post(f"https://api.avito.ru/realty/v1/accounts/{self.__ProfileID}/items/{ItemID}/prices", headers = Headers, json = json.loads(json.dumps(Options)))
		
		# Проверка ответа.
		if Response.status_code != 200:
			# Переключение статуса запроса.
			IsSuccess = False
			# Конвертирование даты.
			StringDate = Date.date()
			# Запись в лог ошибки: не удалось изменить свойства.
			logging.error(f"Profile: {self.__ProfileID}. Unable to change properties for date: \"{Date}\". Response code: " + str(Response.status_code) + ".")
			
		else:
			# Запись в лог сообщения: свойства даты изменены.
			logging.error(f"Profile: {self.__ProfileID}. Properties for date \"{Date}\" changed.")
			
		return IsSuccess
	
	# Задаёт стоимость объявлению с указанным ID.
	def setPrice(self, ItemID: str, Price: int | str) -> bool:
		# Заголовки запроса.
		Headers = {
			"authorization": self.getAccessToken()
		}
		# Состояние: успешен ли запрос.
		IsSuccess = True
		# Отправка запроса на изменение стоимости.
		Response = self.__Session.post(f"https://api.avito.ru/realty/v1/items/{ItemID}/base", headers = Headers, json = json.loads("{\"night_price\": " + str(Price) + "}"))
		
		# Проверка ответа.
		if Response.status_code != 200:
			# Переключение статуса запроса.
			IsSuccess = False
			# Запись в лог ошибки: не удалось изменить стоимость.
			logging.error(f"Profile: {self.__ProfileID}. Unable to change price. Response code: " + str(Response.status_code) + ".")
		
		return IsSuccess
	
	# Увеличивает или уменьшает стоимость объявления с указанным ID.
	def setDeltaPrice(self, ItemID: str, DeltaPrice: int | str) -> bool:
		# Состояние: успешен ли запрос.
		IsSuccess = True
		# Исходная стоимость.
		Price = self.getPrice(ItemID)
		# Вычисление новой стоимости.
		Price += DeltaPrice
		
		# Если цена меньше нуля.
		if Price < 0:
			# Переключение состояния.
			IsSuccess = False
			
		else:
			# Изменение стоимости.
			IsSuccess = self.setPrice(ItemID, Price)
		
		return IsSuccess