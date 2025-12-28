import xml.etree.ElementTree as ET
from xml.dom import minidom
import datetime
from typing import List, Dict, Any


class XMLSerializer:
    @staticmethod
    def _prettify(elem):
        """Возвращает красиво отформатированную XML строку."""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @staticmethod
    def save_groups_to_xml(groups_data: List[str], filename: str) -> bool:
        """Сохраняет список групп в XML файл."""
        try:
            root = ET.Element("Groups")
            root.set("exported", datetime.datetime.now().isoformat())
            root.set("count", str(len(groups_data)))

            for i, group_name in enumerate(groups_data, 1):
                group_elem = ET.SubElement(root, "Group")
                group_elem.set("id", str(i))
                ET.SubElement(group_elem, "Name").text = group_name

            # Сохраняем с форматированием
            xml_str = XMLSerializer._prettify(root)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            return True
        except Exception as e:
            print(f"XML groups serialization error: {e}")
            return False

    @staticmethod
    def save_students_to_xml(students_data: List[tuple], filename: str) -> bool:
        """Сохраняет список студентов в XML файл."""
        try:
            root = ET.Element("Students")
            root.set("exported", datetime.datetime.now().isoformat())
            root.set("count", str(len(students_data)))

            for i, student in enumerate(students_data, 1):
                student_elem = ET.SubElement(root, "Student")
                student_elem.set("id", str(i))

                group, surname, name, patronymic = student
                ET.SubElement(student_elem, "Group").text = group
                ET.SubElement(student_elem, "Surname").text = surname
                ET.SubElement(student_elem, "Name").text = name
                ET.SubElement(student_elem, "Patronymic").text = patronymic

            xml_str = XMLSerializer._prettify(root)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            return True
        except Exception as e:
            print(f"XML students serialization error: {e}")
            return False

    @staticmethod
    def save_journal_to_xml(journal_data: List[tuple], filename: str) -> bool:
        """Сохраняет журнал посещений в XML файл."""
        try:
            root = ET.Element("AttendanceJournal")
            root.set("exported", datetime.datetime.now().isoformat())
            root.set("count", str(len(journal_data)))

            for i, record in enumerate(journal_data, 1):
                record_elem = ET.SubElement(root, "Record")
                record_elem.set("id", str(i))

                # Предполагаем структуру: (date, group, surname, name, patronymic, lesson, missed_hours)
                ET.SubElement(record_elem, "Date").text = str(record[0])
                ET.SubElement(record_elem, "Group").text = str(record[1])
                ET.SubElement(record_elem, "Surname").text = str(record[2])
                ET.SubElement(record_elem, "Name").text = str(record[3])
                ET.SubElement(record_elem, "Patronymic").text = str(record[4])
                ET.SubElement(record_elem, "Lesson").text = str(record[5])
                ET.SubElement(record_elem, "MissedHours").text = str(record[6])

            xml_str = XMLSerializer._prettify(root)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            return True
        except Exception as e:
            print(f"XML journal serialization error: {e}")
            return False

    @staticmethod
    def load_from_xml(filename: str) -> Dict[str, Any]:
        """Загружает данные из XML файла (базовый парсинг)."""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()

            data = {
                'root_tag': root.tag,
                'attributes': dict(root.attrib),
                'children_count': len(root),
                'data': []
            }

            # Простой парсинг для демонстрации
            for child in root:
                child_data = {
                    'tag': child.tag,
                    'attrs': dict(child.attrib),
                    'text': child.text if child.text else '',
                    'children': []
                }

                for subchild in child:
                    child_data['children'].append({
                        'tag': subchild.tag,
                        'text': subchild.text if subchild.text else ''
                    })

                data['data'].append(child_data)

            return data
        except Exception as e:
            print(f"XML deserialization error: {e}")
            return None