import os
from typing import Dict, List, Optional, Tuple

import psycopg2
from dotenv import load_dotenv

from modules.api_module import APIClient
from modules.db_module import DBManager

load_dotenv()

COMPANY_IDS = [205, 947, 871, 581458, 50697, 3749818, 3767717, 28250, 3464728, 2443495]
api_client = APIClient()


def create_database_if_not_exists() -> None:
    """
    Проверяет наличие бд 'vacancy' и создает ее если надо
    """
    conn_params: Dict[str, str] = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
    }

    try:
        conn = psycopg2.connect(dbname='postgres', **conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname='vacancy';")
        exists: Optional[Tuple] = cur.fetchone()

        if not exists:
            print("БД создание 'vacancy'...")
            cur.execute("CREATE DATABASE vacancy;")
        else:
            print("БД 'vacancy' существует.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Ошибка: {e}")


def format_salary(salary_from: Optional[str], salary_to: Optional[str]) -> str:
    """
    Форматер строкового отобраджения
    """
    try:
        from_value: Optional[float] = float(salary_from) if salary_from is not None else None
        to_value: Optional[float] = float(salary_to) if salary_to is not None else None
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


def initialize_database(db_manager: DBManager) -> None:
    """
    Создает таблицы и заполняет их данными о компаниях и вакансиях
    """
    print("Создаем таблицы...")
    db_manager.create_tables()

    print("Загружаем данные о компаниях...")
    companies_data: List[Dict] = api_client.get_companies(COMPANY_IDS)

    for company in companies_data:
        db_manager.insert_company(company)

    for company in companies_data:
        company_id: int = company['id']
        print(f"Загружаем вакансии для компании {company['name']} (ID: {company_id})...")
        vacancies: List[Dict] = api_client.get_vacancies_for_company(company_id)
        for vacancy in vacancies:
            db_manager.insert_vacancy(vacancy)


def user_interaction(db_manager: DBManager) -> None:
    """
    Взатмодействие с юзером
    """
    while True:
        print("\nВыберите действие:")
        print("1. Посмотреть список всех вакансий")
        print("2. Посмотреть среднюю зарплату по вакансиям")
        print("3. Посмотреть вакансии с зарплатой выше средней")
        print("4. Искать вакансии по ключевому слову")
        print("5. Посмотреть компании и количество их вакансий")
        print("6. Выйти из программы")

        choice: str = input("Введите номер действия (1-6): ")

        if choice == '1':
            vacancies: List[Tuple] = db_manager.get_all_vacancies()
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
            avg_salary: Optional[float] = db_manager.get_avg_salary()
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
            keyword: str = input("Введите ключевое слово для поиска вакансий: ")
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
            companies_vacancies: List[Tuple[str, int]] = db_manager.get_companies_and_vacancies_count()
            if companies_vacancies:
                print("\nКомпании и количество их вакансий:")
                for company, count in companies_vacancies:
                    print(f"{company}: {count} вакансий")
            else:
                print("Нет данных о компаниях или вакансиях.")

        elif choice == '6':
            print("Выход из программы.")
            break
        else:
            print("Некорректный ввод. выберите число от 1 до 6.")


def main() -> None:
    """
    Основная функция запуска программы
    """
    create_database_if_not_exists()

    db_params: Dict[str, Optional[str]] = {
        'db_name': 'vacancy',
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 5432))
    }

    db_manager = DBManager(**db_params)
    initialize_database(db_manager)
    user_interaction(db_manager)
    db_manager.close()


if __name__ == "__main__":
    main()
