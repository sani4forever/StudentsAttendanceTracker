import sqlite3
from abc import ABC, abstractmethod
from random import randint

from src.utils.logger import setup_logger

logger = setup_logger()

class DatabaseTables:
    Dates = "Dates"
    Groups = "Groups"
    Students = "Students"
    Lessons = "Lessons"
    Journal = "Journal"
    All = (Dates, Groups, Students, Lessons, Journal)

class IDatabase(ABC):
    @abstractmethod
    def create(self): pass

    @abstractmethod
    def close(self): pass


class DatabaseWork(IDatabase):
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._db = sqlite3.connect(db_file)
        logger.info(f"Connected to database: {db_file}")

    def create(self):
        try:
            self._db.execute("""
            CREATE TABLE "Dates" (
                "id_date" INTEGER NOT NULL,
                "date"    DATE,

                PRIMARY KEY("id_date" AUTOINCREMENT)
            );
            """)
            self._db.execute("""
            CREATE TABLE "Groups" (
                "id_group" INTEGER NOT NULL,
                "group"    varchar(255),

                PRIMARY KEY("id_group" AUTOINCREMENT)
            );
            """)
            self._db.execute("""
            CREATE TABLE "Students" (
                "id_person"  INTEGER NOT NULL,
                "group"      varchar(255),
                "surname"    varchar(255),
                "name"       varchar(255),
                "patronymic" varchar(255),

                PRIMARY KEY("id_person" AUTOINCREMENT)
            );
            """)
            self._db.execute("""
            CREATE TABLE "Lessons" (
                "id_lesson" INTEGER NOT NULL,
                "lesson"      varchar(255),

                PRIMARY KEY("id_lesson" AUTOINCREMENT)
            );
            """)
            self._db.execute("""
            CREATE TABLE "Journal" (
                "id"           INTEGER NOT NULL,
                "date"         DATE,
                "group"        varchar(255),
                "surname"      varchar(255),
                "name"         varchar(255),
                "patronymic"   varchar(255),
                "lesson"       varchar(255),
                "missed_hours" INTEGER,

                PRIMARY KEY("id" AUTOINCREMENT)
            );
            """)
            self._db.commit()
            print("db was created")
        except sqlite3.OperationalError:
            print("db already exists")

    @staticmethod
    def _fixing(values: list[tuple]) -> list[tuple]:
        """"""

        """
        >>> students = []
        >>> for value in values:
        >>>     temp = []
        >>>     for entry in value:  # noqa
        >>>         if chr(774) in entry:  # noqa
        >>>             temp2 = []
        >>>             for ind, letter in enumerate(entry):  # noqa
        >>>                 if letter == chr(774):
        >>>                     temp2[-1] = "й"
        >>>                     continue
        >>>                 temp2.append(letter)
        >>>             entry = "".join(temp2)
        >>>         temp.append(entry)  # noqa
        >>>     students.append(tuple(temp))
        >>> return students
        """

        return [tuple(
            ("".join("й" if entry[i] == "и" and entry[i + 1] == chr(774)
                     else "" if entry[i] == chr(774)
            else entry[i] for i in range(len(entry)))) if not isinstance(entry, int) else entry
            for entry in value)
            for value in values]

    def having(self, table: str, values: dict[str, str]) -> bool:
        cursor = self._db.cursor()
        command = f'SELECT COUNT(*) FROM "{table}" '
        values = [(k, v) for k, v in values.items()]
        command += f'WHERE "{values[0][0]}" IS "{values[0][1]}" '
        if len(values) > 1:
            for column, value in values[1:]:
                command += f'AND "{column}" IS "{value}" '
        command += ";"
        cursor.execute(command)
        result = bool(cursor.fetchone()[0])
        cursor.close()
        return result

    def having_individual_return(self, table: str, columns: list[str], order_by: list[str] = None) -> list[tuple]:
        cursor = self._db.cursor()
        columns = [f'"{i}"' for i in columns]
        command = f'SELECT DISTINCT {", ".join(columns)} FROM "{table}" '
        if order_by:
            order_by = [f'"{i}"' for i in order_by]
            command += f'ORDER BY {", ".join(order_by)} '
        command += ";"
        cursor.execute(command)
        result = cursor.fetchall()
        cursor.close()
        # return self._fixing(result)
        return result

    def select_where(self, table: str, columns: list[str], values: dict[str, str], order_by: list[str] = None) -> list[
        tuple]:
        cursor = self._db.cursor()
        columns = [f'"{i}"' for i in columns]
        command = f'SELECT {", ".join(columns)} FROM "{table}" '
        values = [(k, v) for k, v in values.items()]
        command += f'WHERE "{values[0][0]}" LIKE "{values[0][1]}%" '
        if len(values) > 1:
            for column, value in values[1:]:
                command += f'AND "{column}" IS "{value}" '
        if order_by:
            order_by = [f'"{i}"' for i in order_by]
            command += f'ORDER BY {", ".join(order_by)} '
        command += ";"
        cursor.execute(command)
        result = cursor.fetchall()
        cursor.close()
        # return self._fixing(result)
        return result

    def _insert(self, table: str, values: list[str | int], autocommit: bool = True) -> None:
        if table == "Journal":
            table_info = ('("date", "group", "surname", "name", "patronymic", '
                          '"lesson", "missed_hours") '
                          'VALUES (?, ?, ?, ?, ?, ?, ?)')
        elif table == "Students":
            table_info = ('("group", "surname", "name", "patronymic") '
                          'VALUES (?, ?, ?, ?)')
        elif table == "Groups":
            table_info = '("group") VALUES (?)'
        elif table == "Dates":
            table_info = '("date") VALUES (?)'
        elif table == "Lessons":
            table_info = '("lesson") VALUES (?)'
        else:
            raise ValueError(f'Unknown table {table}')
        self._db.execute(f'INSERT INTO {table} '
                         f'{table_info}', tuple(values))

        if autocommit:
            self._db.commit()

    def insert_date(self, year: str | int, month: str | int, day: str | int, autocommit: bool = True) -> bool:
        # TODO: what if we don't wanna add all lessons on this date?
        # Maybe add prop "lessons"=Lessons.ALL
        # TODO: add class Lessons or similar for constants?
        month = f"0{int(month)}" if int(month) < 10 else month
        day = f"0{int(day)}" if int(day) < 10 else day
        date = f"{year}-{month}-{day}"
        having = self.having("Dates", {"date": date})
        if not having:
            self._insert("Dates", [date], False)
            # students = self._fixing(self.having_individual_return(
            #     "Students",
            #     ["group", "surname", "name", "patronymic"],
            #     ["group", "surname", "name", "patronymic"]))
            students = self.having_individual_return(
                "Students",
                ["group", "surname", "name", "patronymic"],
                ["group", "surname", "name", "patronymic"])
            lessons = [i[0] for i in self.having_individual_return("Lessons", ["lesson"], ["lesson"])]
            for student in students:
                for lesson in lessons:
                    self._insert("Journal", [date, *student, lesson, "-"], False)
            if autocommit:
                self._db.commit()
        return not having

    def insert_group(self, group: str) -> bool:
        having = self.having("Groups", {"group": group})
        if not having:
            self._insert("Groups", [group])
        return not having

    def insert_student(self, group: str, surname: str, name: str, patronymic: str,
                       create_journal_entries: bool = True) -> bool:
        info = {
            "group": group,
            "surname": surname,
            "name": name,
            "patronymic": patronymic
        }
        having = self.having("Students", info)
        if not having:
            self._insert("Students", [group, surname, name, patronymic])

        # Если нужно, создаем записи в журнале
        if create_journal_entries:
            self._create_journal_entries_for_student(group, surname, name, patronymic)
        return not having

    def _create_journal_entries_for_student(self, group: str, surname: str, name: str, patronymic: str):
        """Создать записи в журнале для студента"""
        try:
            # Получаем все даты
            dates = self.having_individual_return("Dates", ["date"], ["date"])
            if not dates:
                print("No dates found in database")
                return

            # Получаем все предметы
            lessons = self.having_individual_return("Lessons", ["lesson"], ["lesson"])
            if not lessons:
                print("No lessons found in database")
                return

            print(f"Creating journal entries for student {surname} {name} {patronymic}")
            print(f"Dates: {len(dates)}, Lessons: {len(lessons)}")

            entries_created = 0
            for date_tuple in dates:
                date = date_tuple[0]
                for lesson_tuple in lessons:
                    lesson = lesson_tuple[0]

                    # Проверяем, нет ли уже такой записи
                    existing = self.having("Journal", {
                        "date": date,
                        "group": group,
                        "surname": surname,
                        "name": name,
                        "patronymic": patronymic,
                        "lesson": lesson
                    })

                    if not existing:
                        self._insert("Journal", [date, group, surname, name, patronymic, lesson, "-"], False)
                        entries_created += 1

            # Коммитим изменения
            self._db.commit()
            print(f"Created {entries_created} journal entries for student {surname} {name} {patronymic}")

        except Exception as e:
            print(f"Error creating journal entries for student: {e}")
            self._db.rollback()
            raise

    def insert_lesson(self, lesson: str) -> bool:
        having = self.having("Lessons", {"lesson": lesson})
        if not having:
            self._insert("Lessons", [lesson])
        return not having

    def insert_journal(self):  # TODO: insert journal
        pass

    def update_date(self,
                    old_year: str | int, old_month: str | int, old_day: str | int,
                    new_year: str | int, new_month: str | int, new_day: str | int,
                    autocommit: bool = True):
        def month_day_fix(value: str) -> str:
            return f"0{int(value)}" if int(value) < 10 else value

        old_month = month_day_fix(old_month)
        old_day = month_day_fix(old_day)
        new_month = month_day_fix(new_month)
        new_day = month_day_fix(new_day)
        old = f"{old_year}-{old_month}-{old_day}"
        new = f"{new_year}-{new_month}-{new_day}"
        if old == new:
            raise ValueError(f"Dates {old} and {new} are identical")
        if not self.having("Dates", {"date": old}):
            raise ValueError(f'Date {old} not found')
        if self.having("Dates", {"date": new}):
            raise ValueError(f'Date {new} already exists')
        self._db.execute(f'UPDATE "Dates" SET "date" = "{new}" WHERE "date" = "{old}"')
        self._db.execute(f'UPDATE "Journal" SET "date" = "{new}" WHERE "date" = "{old}"')
        if autocommit:
            self._db.commit()

    def update_group(self, old: str, new: str):
        if old == new:
            raise ValueError(f'Groups {old} and {new} are identical')
        if not self.having("Groups", {"group": old}):
            raise ValueError(f'Group {old} not found')
        if self.having("Groups", {"group": new}):
            raise ValueError(f'Group {new} already exists')
        self._db.execute(f'UPDATE "Groups" SET "group" = "{new}" WHERE "group" = "{old}"')
        self._db.execute(f'UPDATE "Students" SET "group" = "{new}" WHERE "group" = "{old}"')
        self._db.execute(f'UPDATE "Journal" SET "group" = "{new}" WHERE "group" = "{old}"')
        self._db.commit()

    def update_student(self,
                       old_group: str, old_surname: str, old_name: str, old_patronymic: str,
                       new_group: str, new_surname: str, new_name: str, new_patronymic: str):
        if (old_group == new_group
                and old_surname == new_surname
                and old_name == new_name
                and old_patronymic == new_patronymic):
            raise ValueError(f'Students {old_surname} {old_name} {old_patronymic} '
                             f'and {new_surname} {new_name} {new_patronymic} are identical')
        if not self.having("Students", {"group": old_group,
                                        "surname": old_surname,
                                        "name": old_name,
                                        "patronymic": old_patronymic}):
            raise ValueError(f'Student {old_surname} {old_name} {old_patronymic} in group {old_group} not found')
        if self.having("Students", {"group": new_group,
                                    "surname": new_surname,
                                    "name": new_name,
                                    "patronymic": new_patronymic}):
            raise ValueError(f'Student {new_surname} {new_name} {new_patronymic} in group {new_group} already exists')
        self._db.execute(f'''
        UPDATE "Students"
        SET "group" = "{new_group}",
            "surname" = "{new_surname}",
            "name" = "{new_name}",
            "patronymic" = "{new_patronymic}"
        WHERE "group" = "{old_group}" AND
              "surname" = "{old_surname}" AND
              "name" = "{old_name}" AND
              "patronymic" = "{old_patronymic}"
        ;''')
        self._db.execute(f'''
        UPDATE "Journal"
        SET "group" = "{new_group}",
            "surname" = "{new_surname}",
            "name" = "{new_name}",
            "patronymic" = "{new_patronymic}"
        WHERE "group" = "{old_group}" AND
              "surname" = "{old_surname}" AND
              "name" = "{old_name}" AND
              "patronymic" = "{old_patronymic}"
        ;''')
        self._db.commit()

    def update_lesson(self, old: str, new: str):
        if old == new:
            raise ValueError(f'Lessons {old} and {new} are identical')
        if not self.having("Lessons", {"lesson": old}):
            raise ValueError(f'Lesson {old} not found')
        if self.having("Lessons", {"lesson": new}):
            raise ValueError(f'Lesson {new} already exists')
        self._db.execute(f'UPDATE "Lessons" SET "lesson" = "{new}" WHERE "lesson" = "{old}"')
        self._db.execute(f'UPDATE "Journal" SET "lesson" = "{new}" WHERE "lesson" = "{old}"')
        self._db.commit()

    def update_journal(
            self,
            old_date, old_group, old_surname, old_name, old_patronymic, old_lesson, old_missed_hours,
            new_date, new_group, new_surname, new_name, new_patronymic, new_lesson, new_missed_hours
    ):
        old_data = {
            "date": old_date,
            "group": old_group,
            "surname": old_surname,
            "name": old_name,
            "patronymic": old_patronymic,
            "lesson": old_lesson,
            "missed_hours": old_missed_hours
        }
        new_data = {
            "date": new_date,
            "group": new_group,
            "surname": new_surname,
            "name": new_name,
            "patronymic": new_patronymic,
            "lesson": new_lesson,
            "missed_hours": new_missed_hours
        }
        if old_data == new_data:
            raise ValueError("Presented old and new data are identical")
        if not self.having("Journal", old_data):
            raise ValueError("Presented old data are not found")
        if self.having("Journal", new_data):
            raise ValueError("Presented new data are already exists")
        self._db.execute(f'''
        UPDATE "Journal"
        SET "date" = "{new_date}",
            "group" = "{new_group}",
            "surname" = "{new_surname}",
            "name" = "{new_name}",
            "patronymic" = "{new_patronymic}",
            "lesson" = "{new_lesson}",
            "missed_hours" = "{new_missed_hours}"
        WHERE "date" = "{old_date}" AND
              "group" = "{old_group}" AND
              "surname" = "{old_surname}" AND
              "name" = "{old_name}" AND
              "patronymic" = "{old_patronymic}" AND
              "lesson" = "{old_lesson}" AND
              "missed_hours" = "{old_missed_hours}"
        ;''')
        self._db.commit()

    def delete_date(self, year: str | int, month: str | int, day: str | int,
                    autocommit: bool = True):
        month = f"0{int(month)}" if int(month) < 10 else month
        day = f"0{int(day)}" if int(day) < 10 else day
        date = f"{year}-{month}-{day}"
        if not self.having("Dates", {"date": date}):
            raise ValueError(f'Date {date} not found')
        self._db.execute(f'DELETE FROM "Dates" WHERE "date" = "{date}"')
        self._db.execute(f'DELETE FROM "Journal" WHERE "date" = "{date}"')
        if autocommit:
            self._db.commit()

    def delete_group(self, group: str):
        if not self.having("Groups", {"group": group}):
            raise ValueError(f'Group {group} not found')
        self._db.execute(f'DELETE FROM "Groups" WHERE "group" = "{group}"')
        self._db.execute(f'DELETE FROM "Students" WHERE "group" = "{group}"')
        self._db.execute(f'DELETE FROM "Journal" WHERE "group" = "{group}"')
        self._db.commit()

    def delete_student(self, group: str, surname: str, name: str, patronymic: str):
        if not self.having("Students", {"group": group,
                                        "surname": surname,
                                        "name": name,
                                        "patronymic": patronymic}):
            raise ValueError(f'Student {surname} {name} {patronymic} in group {group} not found')
        self._db.execute(f'''
        DELETE FROM "Students"
        WHERE "group" = "{group}" AND
              "surname" = "{surname}" AND
              "name" = "{name}" AND
              "patronymic" = "{patronymic}"
        ;''')
        self._db.execute(f'''
        DELETE FROM "Journal"
        WHERE "group" = "{group}" AND
              "surname" = "{surname}" AND
              "name" = "{name}" AND
              "patronymic" = "{patronymic}"
        ;''')
        self._db.commit()

    def delete_lesson(self, lesson: str):
        if not self.having("Lessons", {"lesson": lesson}):
            raise ValueError(f'Lesson {lesson} not found')
        self._db.execute(f'DELETE FROM "Lessons" WHERE "lesson" = "{lesson}"')
        self._db.execute(f'DELETE FROM "Journal" WHERE "lesson" = "{lesson}"')
        self._db.commit()

    def delete_journal(self):  # TODO: delete journal
        pass

    def test_data(self):
        lessons = [
            'Численные методы', 'Теория информации', 'Разработка приложений в визуальных средах',
            'Физическая культура', 'Алгоритмы и структуры данных',
            'Организация и функционирование ЭВМ и периферийные устройства',
            'Объектно-ориентированные технологии программирования', 'Языки программирования',
            'Теория вероятностей и математическая статистика', 'Философия',
            'Разработка и анализ требований'
        ]

        # Список студентов из всех трёх групп (половина из каждой группы)
        students = [
            # Группа 10701123
            ['10701123', 'Абусаг', 'Закария', 'Фитури'],
            ['10701123', 'Антанович', 'Дмитрий', 'Сергеевич'],
            ['10701123', 'Аронова', 'Екатерина', 'Александровна'],
            ['10701123', 'Бакышмаз', 'Микаил', 'й'],
            ['10701123', 'Барановский', 'Даниил', 'Владимирович'],
            ['10701123', 'Вербицкий', 'Владислав', 'Александрович'],
            ['10701123', 'Гайданович', 'Максим', 'Иванович'],
            ['10701123', 'Куцко', 'Владислав', 'Витальевич'],
            ['10701123', 'Синкевич', 'Андрей', 'Владимирович'],
            ['10701123', 'Шкантов', 'Иван', 'Николаевич'],

            # Группа 10701223
            ['10701223', 'Annaniyazow', 'Guwanch', 'Orazgeldiyewic'],
            ['10701223', 'Амангелдиев', 'Мейлис', 'Тойлыгылыжович'],
            ['10701223', 'Борщёв', 'Алексей', 'Игоревич'],
            ['10701223', 'Гупанов', 'Андрей', 'Русланович'],
            ['10701223', 'Дешко', 'Никита', 'Дмитриевич'],
            ['10701223', 'Канаш', 'Андрей', 'Николаевич'],
            ['10701223', 'Купреева', 'Милана', 'Кирилловна'],
            ['10701223', 'Петраченко', 'Александра', 'Александровна'],
            ['10701223', 'Суббота', 'Анна', 'Михайловна'],
            ['10701223', 'Швед', 'Константин', 'Александрович'],

            # Группа 10701323
            ['10701323', 'Agbonon', 'Kangni', 'Raoul'],
            ['10701323', 'Asyrow', 'Hemra', 'Yagmywic'],
            ['10701323', 'Атаджанов', 'Керим', 'й'],
            ['10701323', 'Гапоненко', 'Олег', 'Владимирович'],
            ['10701323', 'Герасимов', 'Артем', 'Константинович'],
            ['10701323', 'Каминская', 'Софья', 'Дмитриевна'],
            ['10701323', 'Лях', 'Андрей', 'Игоревич'],
            ['10701323', 'Осипов', 'Даниил', 'Игоревич'],
            ['10701323', 'Сапежко', 'Денис', 'Александрович'],
            ['10701323', 'Шлык', 'Дарья', 'Валентиновна'],
        ]

        for day in range(1, 31):
            day = f"0{day}" if day < 10 else day
            self._insert("Dates", [f"2007-09-{day}"], autocommit=False)

        for lesson in lessons:
            self._insert("Lessons", [lesson], autocommit=False)

        for group in ['10701123', '10701223', '10701323']:
            self._insert("Groups", [group], autocommit=False)

        for student in students:
            self._insert("Students", student, autocommit=False)

        for day in range(1, 31):
            day = f"0{day}" if day < 10 else day
            for student in students:
                for lesson in lessons:
                    self._insert("Journal",
                                 [f"2007-09-{day}", *student, lesson, randint(0, 2)],
                                 autocommit=False)

        self._db.commit()
        print("test data inserted")

    def clear(self):
        for i in DatabaseTables.All:
            self._db.execute(f"DROP TABLE {i};")
        self._db.commit()
        print("db was cleared")
        self.create()

    def close(self):
        self._db.close()
