import tkinter as tk
from tkinter import ttk
import re
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter
import nltk
import logging

logging.basicConfig(level=logging.INFO)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logging.info("Downloading necessary punkt data...")
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    logging.info("Downloading necessary punkt_tab data...")
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    logging.info("Downloading necessary stopwords data...")
    nltk.download('stopwords')

class DuplicateWordFinder(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Поиск повторяющихся слов")

        # Словари
        self.text_length = 100  # Длина текста для нормировки
        self.word_counts = {}
        self.word_min_distances = {}  # Добавляем словарь для хранения минимальных расстояний
        self.sorted_words = []

        # Стоп-слова (можно расширить)
        self.stop_words = set(nltk.corpus.stopwords.words('russian'))

        # Настройка растягивания окна
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.stemmer = SnowballStemmer("russian")

        # Метки
        self.input_label = ttk.Label(self, text="Текст:")
        self.input_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.output_label = ttk.Label(self, text="Слова:")
        self.output_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Текстовые поля
        self.input_text = tk.Text(self, wrap=tk.WORD)
        self.input_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.input_text.bind("<Button-1>", self.highlight_word)

        self.output_listbox = tk.Listbox(self, width=40)  # Задали фиксированную ширину
        self.output_listbox.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.output_listbox.bind("<Button-1>", self.highlight_word)

        # Добавляем скроллбары для обоих текстовых полей
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.input_text.yview)
        scroll.grid(row=1, column=0, sticky="nse")
        self.input_text.configure(yscrollcommand=scroll.set)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.output_listbox.yview)
        scroll.grid(row=1, column=1, sticky="nse")
        self.output_listbox.configure(yscrollcommand=scroll.set)

        # Кнопка "Вставить"
        self.paste_button = ttk.Button(self, text="Вставить", command=self.paste_text)
        self.paste_button.grid(row=2, column=0, pady=10, sticky="ew", padx=5)  # Убираем columnspan

        # Кнопка "Анализировать"
        self.analyze_button = ttk.Button(self, text="Анализировать", command=self.analyze_text)
        self.analyze_button.grid(row=2, column=1, pady=10, sticky="ew", padx=5)

        # Кнопки сортировки
        self.sort_frame = ttk.Frame(self)
        self.sort_frame.grid(row=0, column=1, sticky="e", pady=(5, 0))

        self.sort_var = tk.StringVar(value="count")  # Переменная для хранения типа сортировки

        self.sort_by_count_button = ttk.Button(self.sort_frame, text="По частоте",
                                                command=lambda: self.sort_results("count"))
        self.sort_by_count_button.pack(side="left", padx=2)

        self.sort_by_distance_button = ttk.Button(self.sort_frame, text="По близости",
                                                   command=lambda: self.sort_results("distance"))
        self.sort_by_distance_button.pack(side="left", padx=2)

        # Добавляем метки для статистики
        self.char_count_label = ttk.Label(self, text="Кол-во символов с пробелами: -")
        self.char_count_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.char_count_no_spaces_label = ttk.Label(self, text="Кол-во символов без пробелов: -")
        self.char_count_no_spaces_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.word_count_label = ttk.Label(self, text="Кол-во слов: -")
        self.word_count_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Добавляем метку для отображения индекса удобочитаемости
        self.easy_index_label = ttk.Label(self, text="Индекс удобочитаемости: -")
        self.easy_index_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Добавляем метку для отображения индекса туманности
        self.fog_index_label = ttk.Label(self, text="Индекс туманности: -")
        self.fog_index_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Добавляем метки для водности и заспамленности
        self.water_percentage_label = ttk.Label(self, text="Процент водности: -")
        self.water_percentage_label.grid(row=9, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.spam_percentage_label = ttk.Label(self, text="Процент заспамленности: -")
        self.spam_percentage_label.grid(row=10, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Меню
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Правка", menu=self.edit_menu)

        self.edit_menu.add_command(label="Копировать", command=self.copy_text, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Вставить", command=self.paste_text, accelerator="Ctrl+V")
        self.edit_menu.add_command(label="Вырезать", command=self.cut_text, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Выделить все", command=self.select_all, accelerator="Ctrl+A")

        self.bind_all("<KeyPress>", self.key_event_handler, add="+")

    def key_event_handler(self, event):
        if event.keysym != "??":  # Check if keysym is a valid character
            return

        command_pressed = (event.state & 0x100) != 0  # (macOS)
        ctrl_pressed = (event.state & 0x4) != 0  # (Windows/Linux)

        if ctrl_pressed or command_pressed:
            if event.keycode == 67:  # 'c' keycode
                self.copy_text()
            elif event.keycode == 86:  # 'v' keycode
                self.paste_text()
            elif event.keycode == 88:  # 'x' keycode
                self.cut_text()
            elif event.keycode == 65:  # 'a' keycode
                self.select_all()

    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s\-]', ' ', text)  # Keep hyphens
        return text

    def calculate_fog_index(self, text):
        """Рассчитывает индекс туманности Ганнинга."""
        sentences = sent_tokenize(text, language="russian")
        words = word_tokenize(self.preprocess_text(text), language="russian")
        num_sentences = len(sentences)
        num_words = len(words)

        if num_sentences == 0 or num_words == 0:
            return 0

        # ASL (Average Sentence Length)
        asl = num_words / num_sentences

        # Hard Words (слова с 4 и более слогами) - адаптация для русского
        hard_words = 0
        for word in words:
            syllables = 0
            for char in word:
                if char.lower() in 'аеёиоуыэюя':
                    syllables += 1
            if syllables >= 4:
                # Исключения (собственные имена, сложные слова)
                if not (word[0].isupper() or
                        any(part.lower() in word and len(part) > 0 for part in ["-", "–"]) or  # сложные ч-з дефис
                        word.endswith(("ович", "евич", "овна", "евна", "ична", "ьич"))):  # и отчества
                    hard_words += 1

        # PSW (Percentage of Hard Words)
        psw = (hard_words / num_words) * 100 if num_words > 0 else 0

        # Gunning Fog Index
        fog_index = 0.3 * (asl + psw)
        return fog_index

    def help_fog_index(self, fog_index):
        if fog_index < 7:
            return "Простой для чтения текст, подходящий для широкой аудитории."
        if fog_index < 13:
            return "Легко читаемый текст, понятный для большинства взрослых."
        if fog_index < 18:
            return "Текст средней сложности, может потребоваться некоторое усилие для понимания."
        if fog_index < 24:
            return "Текст высокой сложности, подходит для высокообразованных читателей или специалистов в данной области."
        return "Очень сложный текст, который может быть труден для понимания даже для экспертов."

    def count_syllables(self, word):
        """Упрощённый подсчёт слогов: считаем гласные."""
        return len(re.findall(r'[аеёиоуыэюя]', word.lower()))

    def calculate_flesch_index(self, text, russian_adaptation=True):
        """Вычисляет индекс удобочитаемости Флеша."""
        sentences = sent_tokenize(text, language="russian")
        words = word_tokenize(text, language="russian")
        # Исключить знаки препинания
        words = [word for word in words if word.isalnum()]

        num_sentences = len(sentences)
        num_words = len(words)

        if num_sentences == 0 or num_words == 0:
            return 100  # Возвращаем 100 для пустого текста (очень простой)

        total_syllables = sum(self.count_syllables(word) for word in words)

        asl = num_words / num_sentences
        asw = total_syllables / num_words
        if russian_adaptation:
            # Адаптация Мирошниченко
            fre = 208.7 - (1.52 * asl) - (65.14 * asw)
        else:
            fre = 206.835 - (1.015 * asl) - (84.6 * asw)

        # Ограничиваем FRE в пределах [0, 100]
        fre = max(0, min(fre, 100))
        return fre

    def help_flesch(self, score):
        if score >= 90:
            return "Очень легко читается. Понятно 11-летнему школьнику."
        elif score >= 80:
            return "Легко читается. Разговорный стиль."
        elif score >= 70:
            return "Довольно легко читается."
        elif score >= 60:
            return "Стандартный текст. Понятно 13-15-летним школьникам."
        elif score >= 50:
            return "Довольно сложно читается."
        elif score >= 30:
            return "Сложно читается. Лучше иметь высшее образование."
        else:
            return "Очень сложно читается. Лучше иметь ученую степень."


    def calculate_water_percentage(self, words):
        """Вычисляет процент "воды" в тексте."""
        if not words:
            return 0
        stop_word_count = sum(1 for word in words if word in self.stop_words)
        return (stop_word_count / len(words)) * 100

    def calculate_spam_percentage(self, words, word_counts):
        """Вычисляет процент заспамленности текста."""
        if not words:
            return 0

        # Находим наиболее часто встречающееся слово
        if not word_counts:  # Handle empty word_counts
            return 0
        most_common_word_count = max(word_counts.values())


        # Считаем заспамленность как отношение кол-ва самого частого слова к общему числу слов
        return (most_common_word_count / len(words)) * 100



    def analyze_text(self):
        text = self.input_text.get("1.0", tk.END)
        processed_text = self.preprocess_text(text)
        words = word_tokenize(processed_text, language="russian")  # Tokenize with language
        self.text_length = max(len(words), 100)

        stemmed_words = [self.stemmer.stem(word) for word in words]
        self.word_counts = Counter(stemmed_words)
        # Keep only words that occur more than once *after* stemming
        self.word_counts = {word: count for word, count in self.word_counts.items() if count > 1}

        # Удаляем все теги подсветки
        for tag in self.input_text.tag_names():
            self.input_text.tag_remove(tag, "1.0", tk.END)

        word_positions = {}
        char_index = 0
        for i, word in enumerate(words):
            # Находим позицию слова в исходном тексте
            char_index = processed_text.find(word, char_index) # Find in *processed* text
            stemmed_word = stemmed_words[i]
            if stemmed_word in self.word_counts:
                if stemmed_word not in word_positions:
                    word_positions[stemmed_word] = []
                # Добавляем и номер слова, и позицию в тексте
                word_positions[stemmed_word].append(i)
                self.input_text.tag_add(stemmed_word, f"1.0+{char_index}c", f"1.0+{char_index + len(word)}c")
            char_index += len(word)  # Обновляем индекс для следующего поиска

        # Вычисляем минимальные расстояния для каждого слова
        self.word_min_distances = {}
        for word, positions in word_positions.items():
            if len(positions) > 1:
                min_dist = float('inf')
                for i in range(len(positions) - 1):
                    # Используем номера слов для расчета расстояния
                    distance = positions[i + 1] - positions[i]
                    min_dist = min(min_dist, distance)
                self.word_min_distances[word] = min_dist
            else:
                self.word_min_distances[word] = self.text_length  # Если слово встречается только один раз

        # Обновляем статистику
        self.char_count_label.config(text=f"Кол-во символов с пробелами: {len(text)}")
        char_count_no_spaces = len(text.replace(" ", ""))
        self.char_count_no_spaces_label.config(text=f"Кол-во символов без пробелов: {char_count_no_spaces}")
        self.word_count_label.config(text=f"Кол-во слов: {len(words)}")

        # Рассчитываем индекс удобочитаемости и обновляем метку
        easy_index = self.calculate_flesch_index(text)
        self.easy_index_label.config(
            text=f"Индекс удобочитаемости: {easy_index:.2f} - " + self.help_flesch(easy_index))

        # Рассчитываем индекс туманности и обновляем метку
        fog_index = self.calculate_fog_index(text)
        self.fog_index_label.config(text=f"Индекс туманности: {fog_index:.2f} - " + self.help_fog_index(fog_index))

        # Рассчитываем и выводим процент водности
        water_percentage = self.calculate_water_percentage(words)
        water_text = f"Процент водности: {water_percentage:.2f}% - "
        if water_percentage < 15:
            water_text += "Естественное содержание «воды»."
        elif water_percentage < 30:
            water_text += "Превышенное содержание «воды»."
        else:
            water_text += "Высокое содержание «воды»."
        self.water_percentage_label.config(text=water_text)

        # Рассчитываем и выводим процент заспамленности
        spam_percentage = self.calculate_spam_percentage(words, self.word_counts)
        spam_text = f"Процент заспамленности: {spam_percentage:.2f}% - "
        if spam_percentage < 30:
            spam_text += "Естественное содержание ключевых слов."
        elif spam_percentage < 60:
            spam_text += "SEO-оптимизированный текст."
        else:
            spam_text += "Сильно оптимизированный или заспамленный текст."
        self.spam_percentage_label.config(text=spam_text)


        self.sort_results("count")  # Сортируем по умолчанию по частоте
        self.highlight()  # Подсвечиваем все слова при анализе

    def sort_results(self, sort_type):
        if sort_type == "count":
            self.sorted_words = sorted(self.word_counts.items(), key=lambda item: item[1], reverse=True)
        elif sort_type == "distance":
            # Сортируем по минимальному расстоянию, затем по частоте (если расстояния равны)
            self.sorted_words = sorted(self.word_counts.items(),
                                       key=lambda item: (self.word_min_distances[item[0]], -item[1]))

        self.output_listbox.delete(0, tk.END)  # Очистка списка
        for word, count in self.sorted_words:
            self.output_listbox.insert(tk.END, f"{word}: {count}")  # Добавление элемента

    def get_clicked_word(self, event=None):
        if not event:
            return ""
        char = self.input_text.count("1.0", self.input_text.index(f"@{event.x},{event.y}"), "chars")
        if not char:
            return ""
        start_char = char[0]
        text = self.preprocess_text(self.input_text.get("1.0", tk.END))
        if not (start_char >= 0 and start_char < len(text)):
            return ""
        end_char = start_char
        while start_char > 0 and (text[start_char - 1].isalnum() or text[start_char - 1] == "_"):
            start_char -= 1
        while end_char < len(text) and (text[end_char].isalnum() or text[end_char] == "_"):
            end_char += 1
        return self.stemmer.stem(text[start_char:end_char])

    def highlight_word(self, event=None):
        if event:
            selected_word = ""
            if event.widget == self.output_listbox:
                # Получаем позицию клика
                line_number = self.output_listbox.nearest(event.y)
                if 0 <= line_number < len(self.sorted_words):
                    selected_word = self.sorted_words[line_number][0]
            if event.widget == self.input_text:
                selected_word = self.get_clicked_word(event)
                # Установка выделения в output_listbox
                self.output_listbox.selection_clear(0, tk.END)  # Сначала снимаем все выделения
                for i, (word, _) in enumerate(self.sorted_words):
                    if word == selected_word:
                        self.output_listbox.selection_set(i)
                        self.output_listbox.see(i)  # Прокручиваем к выделенному элементу
                        break

            if selected_word in self.word_min_distances:
                self.highlight(selected_word)
        else:
            self.highlight()

    def calculate_intensity(self, word):
        # Рассчитываем интенсивность на основе минимального расстояния
        min_distance = self.word_min_distances.get(word, self.text_length)
        if min_distance == self.text_length:
            normalized_intensity = 0  # если одно вхождение
        else:
            normalized_intensity = int((1.0 - (1.0 - min_distance / self.text_length) ** 2) * 32)  # нормализация
            normalized_intensity = max(1, min(normalized_intensity * 8, 255))  # ограничение
        return normalized_intensity

    def highlight(self, select_word=""):
        for word in self.word_min_distances.keys():
            intensity = self.calculate_intensity(word)
            if word == select_word:
                hex_color = self.get_mark(intensity)
            else:
                hex_color = self.get_color(intensity)
            self.input_text.tag_config(word, background=hex_color)

    def get_color(self, intensity):
        color_b = min(int(128 + (intensity * 0.5)), 255)
        color_r = min(int(128 + (intensity * 0.5)), 255)
        return f"#FF{color_r:02x}{color_b:02x}"

    def get_mark(self, intensity):
        color_b = min(int(64 + (intensity * 0.75)), 255)
        color_r = min(int(196 + (intensity * 0.25)), 255)
        return f"#FF{color_r:02x}{color_b:02x}"

    def paste_text(self, event=None):
        try:
            # If there's a selection, replace it
            if self.input_text.tag_ranges("sel"):
                self.input_text.delete("sel.first", "sel.last")
            text = self.input_text.clipboard_get()
            self.input_text.insert(tk.INSERT, text)
        except tk.TclError:
            print("Буфер обмена пуст или содержит данные не текстового формата.")
        return "break"

    def copy_text(self, event=None):
        try:
            if self.input_text.tag_ranges("sel"):
                self.input_text.clipboard_clear()
                self.input_text.clipboard_append(self.input_text.selection_get())
        except tk.TclError:
            pass  # It's okay if copying fails (e.g., no selection)
        return "break"

    def cut_text(self, event=None):
        try:
            if self.input_text.tag_ranges("sel"):
                self.copy_text()  # Copy first
                self.input_text.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        return "break"

    def select_all(self, event=None):
        self.input_text.tag_add(tk.SEL, "1.0", tk.END)
        self.input_text.mark_set(tk.INSERT, "1.0")
        self.input_text.see(tk.INSERT)
        return "break"


if __name__ == "__main__":
    app = DuplicateWordFinder()
    app.mainloop()