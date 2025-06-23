from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extensions import connection, cursor


class DBManager:
    def __init__(
            self,
            db_name: str,
            user: str,
            password: str,
            host: str = 'localhost',
            port: int = 5432
    ) -> None:
        """
        Инициализация соединения с базой данных PostgreSQL
        """
        self.connection: connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.connection.autocommit = True
        self.cursor: cursor = self.connection.cursor()

    def create_tables(self) -> None:
        """
        Создает таблицы компаний и вакансий
        """
        create_companies_table = '''
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            company_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            url TEXT
        );
        '''

        create_vacancies_table = '''
        CREATE TABLE IF NOT EXISTS vacancies (
            vacancy_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            company_id INTEGER REFERENCES companies(company_id),
            url TEXT,
            salary_from TEXT,
            salary_to TEXT,
            salary_currency TEXT,
            city TEXT,
            experience TEXT,
            employment TEXT,
            schedule TEXT
        );
        '''
        self.cursor.execute(create_companies_table)
        self.cursor.execute(create_vacancies_table)

    def insert_company(self, company_data: dict) -> None:
        """
        Вставляет данные о компании в таблицу
        """
        insert_query = '''
        INSERT INTO companies (company_id, name, url)
        VALUES (%s, %s, %s)
        ON CONFLICT (company_id) DO NOTHING;
        '''
        self.cursor.execute(insert_query, (
            company_data['id'],
            company_data['name'],
            company_data.get('url', '')
        ))

    def insert_vacancy(self, vacancy_data: dict) -> None:
        """
        Вставляет данные о вакансии
        """
        salary_from = vacancy_data['salary']['from'] if vacancy_data['salary'] else None
        salary_to = vacancy_data['salary']['to'] if vacancy_data['salary'] else None
        salary_currency = vacancy_data['salary']['currency'] if vacancy_data['salary'] else None

        insert_query = '''
        INSERT INTO vacancies (vacancy_id, company_id, name, salary_from, salary_to, salary_currency, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vacancy_id) DO NOTHING;
        '''

        self.cursor.execute(insert_query, (
            vacancy_data['id'],
            vacancy_data['employer']['id'],
            vacancy_data['name'],
            salary_from,
            salary_to,
            salary_currency,
            vacancy_data['alternate_url']
        ))

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Возвращает список кортежей с названием компании и количеством вакансий
        """
        query = '''
        SELECT c.name, COUNT(v.vacancy_id) as vacancies_count
        FROM companies c
        LEFT JOIN vacancies v ON c.company_id = v.company_id
        GROUP BY c.name;
        '''
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_all_vacancies(self) -> List[Tuple[str, str, str, str]]:
        """
        Возвращает все вакансии с информацией о компании и зарплате.
        """
        query = '''
            SELECT c.name AS company_name, v.name AS vacancy_name,
                   v.salary_from, v.salary_to,
                   v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id;
        '''
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        processed_results = []
        for row in results:
            company_name = row[0]
            vacancy_name = row[1]
            salary_from = row[2]
            salary_to = row[3]
            url = row[4]

            try:
                sf = float(salary_from) if salary_from is not None else None
                st = float(salary_to) if salary_to is not None else None
            except (TypeError, ValueError):
                sf = None
                st = None

            if sf is not None and st is not None:
                salary_str = f"от {sf} до {st}"
            elif sf is not None:
                salary_str = f"от {sf}"
            elif st is not None:
                salary_str = f"до {st}"
            else:
                salary_str = "Зарплата не указана"

            processed_results.append((company_name, vacancy_name, salary_str, url))

        return processed_results

    def get_avg_salary(self) -> Optional[float]:
        """
        Вычисляет среднюю зарплату по вакансиям
        """
        query = '''
            SELECT AVG((v.salary_from::numeric + v.salary_to::numeric)/2.0) AS avg_salary
            FROM vacancies v
            WHERE v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL;
        '''
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else None

    def get_vacancies_with_higher_salary(self) -> List[Tuple[str, str, str, str]]:
        """
        Возвращает вакансии с зарплатой выше средней
        """
        avg_salary = self.get_avg_salary()
        if avg_salary is None:
            return []

        query = '''
            SELECT c.name AS company_name, v.name AS vacancy_name,
                   v.salary_from, v.salary_to,
                   v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE 
                (v.salary_from::numeric > %s OR v.salary_to::numeric > %s)
                AND (v.salary_from IS NOT NULL OR v.salary_to IS NOT NULL);
        '''
        with self.connection.cursor() as cursor:
            cursor.execute(query, (avg_salary, avg_salary))
            results = cursor.fetchall()

        processed_results = []
        for row in results:
            company_name = row[0]
            vacancy_name = row[1]
            salary_from = row[2]
            salary_to = row[3]
            url = row[4]

            try:
                sf = float(salary_from) if salary_from is not None else None
                st = float(salary_to) if salary_to is not None else None
            except (TypeError, ValueError):
                sf = None
                st = None

            if sf is not None and st is not None:
                salary_str = f"от {sf} до {st}"
            elif sf is not None:
                salary_str = f"от {sf}"
            elif st is not None:
                salary_str = f"до {st}"
            else:
                salary_str = "Зарплата не указана"

            processed_results.append((company_name, vacancy_name, salary_str, url))

        return processed_results

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, str, str, str]]:
        """
        Возвращает вакансии по ключевому слову в названии
        """
        pattern = f'%{keyword}%'
        query = '''
            SELECT c.name AS company_name, v.name AS vacancy_name,
                   v.salary_from, v.salary_to,
                   v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE v.name ILIKE %s;
        '''
        with self.connection.cursor() as cursor:
            cursor.execute(query, (pattern,))
            results = cursor.fetchall()

        processed_results = []
        for row in results:
            company_name = row[0]
            vacancy_name = row[1]
            salary_from = row[2]
            salary_to = row[3]
            url = row[4]

            try:
                sf = float(salary_from) if salary_from is not None else None
                st = float(salary_to) if salary_to is not None else None
            except (TypeError, ValueError):
                sf = None
                st = None

            if sf is not None and st is not None:
                salary_str = f"от {sf} до {st}"
            elif sf is not None:
                salary_str = f"от {sf}"
            elif st is not None:
                salary_str = f"до {st}"
            else:
                salary_str = "Зарплата не указана"

            processed_results.append((company_name, vacancy_name, salary_str, url))

        return processed_results

    def close(self) -> None:
        """
        Закрывает соединение с базой данных
        """
        self.cursor.close()
        self.connection.close()
