"""
Random Task Generator
Консольное приложение для генерации задач с использованием ООП, Factory, JSON и очереди.
"""

import json
import random
from collections import deque
from abc import ABC, abstractmethod


# ------------------- Модель задачи (Task) -------------------
class Task:
    """Базовая модель задачи с описанием, типом и сложностью."""
    
    def __init__(self, description: str, task_type: str, difficulty: int):
        self._description = description          # инкапсуляция
        self._type = task_type
        self._difficulty = difficulty            # уровень сложности 1-5

    # Геттеры
    def get_description(self) -> str:
        return self._description

    def get_type(self) -> str:
        return self._type

    def get_difficulty(self) -> int:
        return self._difficulty

    # Сеттер с валидацией сложности
    def set_difficulty(self, difficulty: int):
        if 1 <= difficulty <= 5:
            self._difficulty = difficulty
        else:
            raise ValueError("Сложность должна быть от 1 до 5")

    def to_dict(self) -> dict:
        """Сериализация задачи в словарь для JSON."""
        return {
            "description": self._description,
            "type": self._type,
            "difficulty": self._difficulty
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Восстановление задачи из словаря."""
        return cls(data["description"], data["type"], data["difficulty"])

    def __str__(self) -> str:
        stars = "★" * self._difficulty + "☆" * (5 - self._difficulty)
        return f"[{self._type}] {self._description} (Сложность: {stars})"


# ------------------- Абстрактный создатель (Factory) -------------------
class TaskCreator(ABC):
    """Абстрактный класс создателя задач (паттерн Factory Method)."""
    
    @abstractmethod
    def create_task(self, description: str, difficulty: int) -> Task:
        pass


# Конкретные создатели для разных типов задач
class WorkTaskCreator(TaskCreator):
    def create_task(self, description: str, difficulty: int) -> Task:
        return Task(description, "Работа", difficulty)


class SportTaskCreator(TaskCreator):
    def create_task(self, description: str, difficulty: int) -> Task:
        return Task(description, "Спорт", difficulty)


class StudyTaskCreator(TaskCreator):
    def create_task(self, description: str, difficulty: int) -> Task:
        return Task(description, "Учеба", difficulty)


class DefaultTaskCreator(TaskCreator):
    def create_task(self, description: str, difficulty: int) -> Task:
        return Task(description, "Разное", difficulty)


# ------------------- Фабрика задач (TaskFactory) -------------------
class TaskFactory:
    """
    Фабрика, которая создаёт задачи через соответствующих создателей.
    Позволяет регистрировать новые типы задач.
    """
    
    def __init__(self):
        self._creators = {
            "Работа": WorkTaskCreator(),
            "Спорт": SportTaskCreator(),
            "Учеба": StudyTaskCreator()
        }

    def register_type(self, type_name: str, creator: TaskCreator):
        """Регистрация нового типа задачи (расширяемость)."""
        self._creators[type_name] = creator

    def create_task(self, task_type: str, description: str, difficulty: int) -> Task:
        """Создаёт задачу указанного типа."""
        creator = self._creators.get(task_type)
        if not creator:
            # Если тип не зарегистрирован, используем DefaultTaskCreator
            creator = DefaultTaskCreator()
        return creator.create_task(description, difficulty)


# ------------------- Хранилище задач (база данных в памяти + JSON) -------------------
class TaskStorage:
    """Управляет списком доступных задач и историей генерации."""
    
    def __init__(self, json_file: str = "task_history.json"):
        self.json_file = json_file
        self.available_tasks = []    # список предопределённых задач
        self.history = deque()       # очередь истории сгенерированных задач (макс. 10)

        self.factory = TaskFactory()
        self._load_tasks_from_json()
        self._load_history_from_json()

    def _load_tasks_from_json(self):
        """Загружает доступные задачи из JSON файла."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Загружаем доступные задачи
                for task_data in data.get("available_tasks", []):
                    task = Task.from_dict(task_data)
                    self.available_tasks.append(task)
        except (FileNotFoundError, json.JSONDecodeError):
            # Если файла нет или он битый — создаём стандартный список задач
            self._create_default_tasks()

    def _create_default_tasks(self):
        """Создаёт набор стандартных задач."""
        self.available_tasks = [
            Task("Сделать отчёт по проекту", "Работа", 4),
            Task("Пробежка 5 км", "Спорт", 3),
            Task("Выучить 20 новых слов", "Учеба", 2),
            Task("Позвонить клиенту", "Работа", 2),
            Task("Йога 30 минут", "Спорт", 1),
            Task("Решить 5 задач по алгоритмам", "Учеба", 5),
            Task("Провести мини-тренировку", "Спорт", 2),
            Task("Написать пост в блог", "Работа", 2)
        ]

    def _load_history_from_json(self):
        """Загружает историю сгенерированных задач из JSON."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for task_data in data.get("history", []):
                    task = Task.from_dict(task_data)
                    self.history.append(task)
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = deque(maxlen=10)

    def save_all_to_json(self):
        """Сохраняет все задачи и историю в JSON."""
        data = {
            "available_tasks": [task.to_dict() for task in self.available_tasks],
            "history": [task.to_dict() for task in self.history]
        }
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_new_task(self, task_type: str, description: str, difficulty: int):
        """
        Добавляет новую задачу в список доступных (с валидацией).
        """
        if not description or len(description.strip()) == 0:
            raise ValueError("Описание задачи не может быть пустым")
        if difficulty < 1 or difficulty > 5:
            raise ValueError("Сложность должна быть от 1 до 5")
        
        new_task = self.factory.create_task(task_type, description.strip(), difficulty)
        self.available_tasks.append(new_task)
        self.save_all_to_json()
        print(f"✓ Задача добавлена: {new_task}")

    def generate_random_task(self) -> Task:
        """Генерирует случайную задачу из доступного списка."""
        if not self.available_tasks:
            raise RuntimeError("Нет доступных задач. Добавьте задачи вручную.")
        
        task = random.choice(self.available_tasks)
        # Добавляем в историю (очередь ограничена 10 элементами)
        self.history.append(task)
        self.save_all_to_json()
        return task

    def filter_tasks(self, task_type: str = None, difficulty: int = None):
        """Фильтрует задачи по типу и/или сложности."""
        result = self.available_tasks[:]
        
        if task_type:
            result = [t for t in result if t.get_type().lower() == task_type.lower()]
        
        if difficulty is not None:
            result = [t for t in result if t.get_difficulty() == difficulty]
        
        return result

    def show_history(self):
        """Показывает последние 10 сгенерированных задач (очередь)."""
        if not self.history:
            print("История пуста.")
        else:
            for i, task in enumerate(self.history, 1):
                print(f"{i}. {task}")


# ------------------- Пользовательский интерфейс (консоль) -------------------
class ConsoleApp:
    """Консольное приложение для управления генерацией задач."""
    
    def __init__(self):
        self.storage = TaskStorage()
        self.valid_types = ["Работа", "Спорт", "Учеба", "Разное"]

    def run(self):
        """Главный цикл приложения."""
        while True:
            self._show_menu()
            choice = input("\nВыберите действие: ").strip()
            
            if choice == "1":
                self._generate_random_task()
            elif choice == "2":
                self._filter_tasks()
            elif choice == "3":
                self._add_new_task()
            elif choice == "4":
                self.storage.show_history()
            elif choice == "5":
                self._show_all_tasks()
            elif choice == "6":
                print("Сохраняем данные и выходим...")
                self.storage.save_all_to_json()
                break
            else:
                print("❌ Ошибка: введите число от 1 до 6.")

    def _show_menu(self):
        print("\n" + "=" * 50)
        print("   ГЕНЕРАТОР СЛУЧАЙНЫХ ЗАДАЧ   ")
        print("=" * 50)
        print("1. 🎲 Сгенерировать случайную задачу")
        print("2. 🔍 Фильтровать задачи по типу/сложности")
        print("3. ➕ Добавить новую задачу")
        print("4. 📜 Показать историю (последние 10)")
        print("5. 📋 Показать все доступные задачи")
        print("6. 💾 Выйти и сохранить")

    def _generate_random_task(self):
        try:
            task = self.storage.generate_random_task()
            print("\n✨ Ваша случайная задача на сегодня:")
            print(f"   {task}")
        except RuntimeError as e:
            print(f"❌ {e}")

    def _filter_tasks(self):
        print("\nФильтрация задач:")
        type_filter = input("Введите тип задачи (Работа/Спорт/Учеба) или Enter для пропуска: ").strip()
        difficulty_filter = input("Введите сложность (1-5) или Enter для пропуска: ").strip()
        
        difficulty = None
        if difficulty_filter:
            try:
                difficulty = int(difficulty_filter)
                if not (1 <= difficulty <= 5):
                    print("❌ Сложность должна быть 1-5. Фильтр по сложности не применяется.")
                    difficulty = None
            except ValueError:
                print("❌ Неверное число. Фильтр по сложности не применяется.")
        
        if not type_filter:
            type_filter = None
        
        filtered = self.storage.filter_tasks(type_filter, difficulty)
        
        if filtered:
            print(f"\n📌 Найдено задач: {len(filtered)}")
            for i, task in enumerate(filtered, 1):
                print(f"{i}. {task}")
        else:
            print("❌ Задачи не найдены.")

    def _add_new_task(self):
        print("\n➕ Добавление новой задачи:")
        
        # Ввод типа с валидацией
        while True:
            task_type = input(f"Тип ({'/'.join(self.valid_types)}): ").strip()
            if task_type in self.valid_types:
                break
            print(f"❌ Неверный тип. Допустимые: {', '.join(self.valid_types)}")
        
        # Ввод описания
        description = input("Описание задачи: ").strip()
        if not description:
            print("❌ Описание не может быть пустым.")
            return
        
        # Ввод сложности с валидацией
        try:
            difficulty = int(input("Сложность (1-5): ").strip())
        except ValueError:
            print("❌ Сложность должна быть числом.")
            return
        
        try:
            self.storage.add_new_task(task_type, description, difficulty)
        except ValueError as e:
            print(f"❌ Ошибка: {e}")

    def _show_all_tasks(self):
        if not self.storage.available_tasks:
            print("📭 Нет доступных задач.")
        else:
            print("\n📋 Все доступные задачи:")
            for i, task in enumerate(self.storage.available_tasks, 1):
                print(f"{i}. {task}")


# ------------------- Точка входа -------------------
if __name__ == "__main__":
    app = ConsoleApp()
    app.run()
