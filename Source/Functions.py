from dublib.Methods import RemoveRecurringSubstrings

import telebot

# Строит список описаний задач.
def BuildTasksDescriptions(Tasks: dict) -> list[str]:
	# Описания задач.
	Descriptions = list()
	
	# Для каждой задачи.
	for TaskID in Tasks.keys():
		# Конвертирование стоимости в строку.
		Price = str(Tasks[TaskID]["method"]["price"])
		
		# Формирование стоимости.
		if Tasks[TaskID]["method"]["delta"] == True and Tasks[TaskID]["method"]["price"] > 0:
			# Добавление символа плюса.
			Price = "\+" + Price
			
		# Буфер описания.
		Bufer = "Идентификатор: " + EscapeCharacters(TaskID) + "\n"
		Bufer += "Профиль Авито: " + Tasks[TaskID]["method"]["profile"] + "\n"
		Bufer += "ID объявления: " + str(Tasks[TaskID]["method"]["item-id"]) + "\n"
		Bufer += "Стоимость: " + EscapeCharacters(Price) + "\n"
		Bufer += "Условие: _каждый " + Tasks[TaskID]["trigger"]["day-of-week"] + " в " + str(Tasks[TaskID]["trigger"]["hour"]) + ":" + str(Tasks[TaskID]["trigger"]["minute"]) + "_\.\n"
		# Сохранение буфера.
		Descriptions.append(Bufer)
		
	return Descriptions

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

# Отправляет сообщение о необходимости регистрации пользователя Telegram.
def UserAuthRequired(Bot: telebot.TeleBot, ChatID: int):
    # Отправка сообщения: необходимо авторизоваться.
	Bot.send_message(
		ChatID,
		"Для использования команд вам необходимо авторизоваться. Пришлите мне пароль к серверу."
	)