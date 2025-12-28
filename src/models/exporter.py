import os
import json
import pickle
import msgpack
from datetime import datetime


class DataExporter:
    """Класс для экспорта данных из базы данных"""

    def __init__(self, db, serializer, xml_serializer, os_module=None):
        """
        Инициализация экспортера

        Args:
            db: Экземпляр DatabaseWork
            serializer: Экземпляр Serializer
            xml_serializer: Экземпляр XMLSerializer
            os_module: Модуль os (для тестирования)
        """
        self.db = db
        self.serializer = serializer
        self.xml_serializer = xml_serializer
        self.os_module = os_module or os

    # --- JSON ЭКСПОРТ ---

    def export_groups_to_json(self, filename="groups_export.json"):
        """Экспорт групп в JSON"""
        if not self.serializer:
            return False, "JSON сериализатор не доступен"

        try:
            data = self.db.having_individual_return("Groups", ["group"])
            groups = [g[0] for g in data]

            if self.serializer.save_to_json(groups, filename):
                return True, f"Группы экспортированы в {filename}"
            else:
                return False, "Ошибка экспорта в JSON"

        except Exception as e:
            return False, f"Ошибка экспорта JSON: {str(e)}"

    # --- XML ЭКСПОРТ ---

    def export_groups_to_xml(self, filename="groups_export.xml"):
        """Экспорт групп в XML"""
        if not self.xml_serializer:
            return False, "XML сериализатор не доступен"

        try:
            data = self.db.having_individual_return("Groups", ["group"])
            groups = [g[0] for g in data]

            if self.xml_serializer.save_groups_to_xml(groups, filename):
                return True, f"Группы экспортированы в XML: {filename}"
            else:
                return False, "Ошибка экспорта в XML"

        except Exception as e:
            return False, f"Ошибка экспорта XML: {str(e)}"

    def export_students_to_xml(self, filename="students_export.xml"):
        """Экспорт студентов в XML"""
        if not self.xml_serializer:
            return False, "XML сериализатор не доступен"

        try:
            data = self.db.having_individual_return(
                "Students",
                ["group", "surname", "name", "patronymic"],
                ["group", "surname", "name", "patronymic"]
            )

            if self.xml_serializer.save_students_to_xml(data, filename):
                return True, f"Студенты экспортированы в XML: {filename}"
            else:
                return False, "Ошибка экспорта студентов в XML"

        except Exception as e:
            return False, f"Ошибка экспорта студентов XML: {str(e)}"

    def export_journal_to_xml(self, filename="journal_export.xml"):
        """Экспорт журнала в XML"""
        if not self.xml_serializer:
            return False, "XML сериализатор не доступен"

        try:
            data = self.db.having_individual_return(
                "Journal",
                ["date", "group", "surname", "name", "patronymic", "lesson", "missed_hours"],
                ["date", "group", "surname", "name", "patronymic"]
            )

            if self.xml_serializer.save_journal_to_xml(data, filename):
                return True, f"Журнал экспортирован в XML: {filename}"
            else:
                return False, "Ошибка экспорта журнала в XML"

        except Exception as e:
            return False, f"Ошибка экспорта журнала XML: {str(e)}"

    # --- БИНАРНЫЙ ЭКСПОРТ ---

    def export_full_backup_to_pickle(self, filename="full_backup.pkl"):
        """Экспорт всех данных в Pickle (бинарный)"""
        if not self.serializer:
            return False, "Сериализатор не доступен"

        try:
            all_data = {
                'groups': self.db.having_individual_return("Groups", ["group"]),
                'students': self.db.having_individual_return(
                    "Students",
                    ["group", "surname", "name", "patronymic"]
                ),
                'lessons': self.db.having_individual_return("Lessons", ["lesson"]),
                'dates': self.db.having_individual_return("Dates", ["date"]),
                'journal': self.db.having_individual_return(
                    "Journal",
                    ["date", "group", "surname", "name", "patronymic", "lesson", "missed_hours"]
                )
            }

            if self.serializer.save_to_pickle(all_data, filename):
                # Получаем информацию о файле
                info = self.serializer.get_file_info(filename)
                size_kb = info['size'] / 1024 if info else 0
                return True, f"Полный бэкап сохранен в Pickle\nРазмер: {size_kb:.2f} KB"
            else:
                return False, "Ошибка экспорта в Pickle"

        except Exception as e:
            return False, f"Ошибка экспорта Pickle: {str(e)}"

    def export_groups_to_msgpack(self, filename="groups_export.msgpack"):
        """Экспорт групп в MessagePack (бинарный, компактный)"""
        if not self.serializer:
            return False, "Сериализатор не доступен"

        try:
            data = self.db.having_individual_return("Groups", ["group"])
            groups = [g[0] for g in data]

            if self.serializer.save_to_msgpack(groups, filename):
                # Сравниваем размеры с JSON
                json_filename = "groups_export.json"
                if self.os_module.path.exists(json_filename):
                    json_size = self.os_module.path.getsize(json_filename)
                    msgpack_size = self.os_module.path.getsize(filename)

                    if json_size > 0:
                        ratio = (1 - msgpack_size / json_size) * 100
                        return True, (
                            f"Группы экспортированы в MessagePack\n"
                            f"Экономия места: {ratio:.1f}% "
                            f"({json_size} bytes → {msgpack_size} bytes)"
                        )

                return True, "Группы экспортированы в MessagePack"
            else:
                return False, "Ошибка экспорта в MessagePack"

        except Exception as e:
            return False, f"Ошибка экспорта MessagePack: {str(e)}"

    # --- УТИЛИТНЫЕ МЕТОДЫ ---

    def get_export_formats(self):
        """Возвращает список поддерживаемых форматов экспорта"""
        return {
            'json': ['groups'],
            'xml': ['groups', 'students', 'journal'],
            'pickle': ['full_backup'],
            'msgpack': ['groups']
        }

    def get_file_size(self, filename):
        """Получить размер файла"""
        try:
            if self.os_module.path.exists(filename):
                size = self.os_module.path.getsize(filename)
                if size < 1024:
                    return f"{size} bytes"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.2f} KB"
                else:
                    return f"{size / (1024 * 1024):.2f} MB"
            return "Файл не найден"
        except:
            return "Не удалось определить размер"