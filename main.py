import os
from typing import Dict, Optional

from dotenv import load_dotenv

from db_module import DBManager

load_dotenv()

COMPANY_IDS = [205, 947, 871, 581458, 50697, 3749818, 3767717, 28250, 3464728, 2443495]


def format_salary(salary_from: Optional[str], salary_to: Optional[str]) -> str:
    """
    Форматирует диапазон зарплаты в строку для отображения
    """
    try:
        from_value = float(salary_from) if salary_from is not None else None
        to_value = float(salary_to) if salary_to is not None else None
    except (TypeError, ValueError):
        return "Зарплата не указана"

    if from_value and to_value:
        return f"от {from_value} до {to_value}"
    elif from_value:
        return f"от {from_value}"
    elif to_value:
        return f"до {to_value}"
    else:
        return "Зарплата не указана"


def user_interaction(db_manager: DBManager) -> None:
    """
    Обеспечивает взаимодействие с пользователем через консольное меню
    """
    while True:
        print("\nВыберите действие:")
        print("1. Посмотреть список всех вакансий")
        print("2. Посмотреть среднюю зарплату по вакансиям")
        print("3. Посмотреть вакансии с зарплатой выше средней")
        print("4. Искать вакансии по ключевому слову")
        print("5. Посмотреть компании и количество их вакансий")
        print("6. Выйти из программы")
        choice = input("Введите номер действия (1-6): ")

        if choice == '1':
            vacancies = db_manager.get_all_vacancies()
            if vacancies:
                print("\nВсе вакансии:")
                for row in vacancies:
                    if len(row) >= 6:
                        company_name = row[0]
                        vacancy_name = row[1]
                        salary_range = format_salary(row[2], row[3])
                        url = row[5]
                        print(
                            f"Компания: {company_name}\nВакансия: {vacancy_name}\nЗарплата:"
                            f" {salary_range}\nПодробнее: {url}\n"
                        )
                    else:
                        print(f"Данные о вакансии: {row}")
            else:
                print("Нет данных о вакансиях.")

        elif choice == '2':
            avg_salary = db_manager.get_avg_salary()
            if avg_salary is not None:
                print(f"\nСредняя зарплата по вакансиям составляет: {avg_salary:.2f}")
            else:
                print("Нет данных для расчета средней зарплаты.")

        elif choice == '3':
            vacancies = db_manager.get_vacancies_with_higher_salary()
            if vacancies:
                print("\nВакансии с зарплатой выше средней:")
                for row in vacancies:
                    if len(row) >= 6:
                        company_name = row[0]
                        vacancy_name = row[1]
                        salary_range = format_salary(row[2], row[3])
                        url = row[5]
                        print(
                            f"Компания: {company_name}\nВакансия: {vacancy_name}\nЗарплата:"
                            f" {salary_range}\nПодробнее: {url}\n"
                        )
                    else:
                        print(f"Данные о вакансии неполные: {row}")
            else:
                print("Нет вакансий с зарплатой выше средней или данных нет.")

        elif choice == '4':
            keyword = input("Введите ключевое слово для поиска вакансий: ")
            vacancies = db_manager.get_vacancies_with_keyword(keyword)
            if vacancies:
                print(f"\nВакансии содержащие слово '{keyword}':")
                for row in vacancies:
                    if len(row) >= 6:
                        company_name = row[0]
                        vacancy_name = row[1]
                        salary_range = format_salary(row[2], row[3])
                        url = row[5]
                        print(
                            f"Компания: {company_name}\nВакансия: {vacancy_name}\nЗарплата:"
                            f" {salary_range}\nПодробнее: {url}\n"
                        )
                    else:
                        print(f"Данные о вакансии: {row}")
            else:
                print(f"Вакансий по ключевому слову '{keyword}' не найдено.")

        elif choice == '5':
            companies_vacancies = db_manager.get_companies_and_vacancies_count()
            if companies_vacancies:
                print("\nКомпании и количество их вакансий:")
                for company, count in companies_vacancies:
                    print(f"{company}: {count} вакансий")
            else:
                print("Нет данных о компаниях или вакансиях.")

        elif choice == '6':
            print("Выход")
            break
        else:
            print("Некорректный ввод. выберите число от 1 до 6.")


def main() -> None:
    """
    Основная функция запуска программы
    Загружает параметры соединения и инициирует взаимодействие с пользователем
    """
    db_params: Dict[str, Optional[str]] = {
        'db_name': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 5432))
    }

    db_manager = DBManager(**db_params)

    user_interaction(db_manager)

    db_manager.close()


if __name__ == "__main__":
    main()
