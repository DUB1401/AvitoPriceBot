from dublib.Methods import RemoveRecurringSubstrings

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