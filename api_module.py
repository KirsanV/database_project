import time
from typing import Dict, List, Optional

import requests

API_URL = "https://api.hh.ru"


def get_companies(ids: List[int]) -> List[Dict]:
    """
    Получает информацию о компаниях по списку их id
    """
    companies: List[Dict] = []
    for company_id in ids:
        response = requests.get(f"{API_URL}/employers/{company_id}")
        if response.status_code == 200:
            companies.append(response.json())
        else:
            print(f"Ошибка получения данных о компании {company_id}")
        time.sleep(0.2)
    return companies


def get_vacancies_for_company(
    company_id: int,
    per_page: int = 50,
    pages: int = 1
) -> List[Dict]:
    """
    Получает вакансии для компании по её id
    """
    vacancies: List[Dict] = []
    for page in range(pages):
        params: Dict[str, int] = {
            'employer_id': company_id,
            'per_page': per_page,
            'page': page
        }
        response = requests.get(f"{API_URL}/vacancies", params=params)
        if response.status_code == 200:
            data = response.json()
            vacancies.extend(data['items'])
            if data['pages'] <= page + 1:
                break
        else:
            print(f"Ошибка получения вакансий для компании {company_id}")
        time.sleep(0.2)
    return vacancies


def get_vacancy_details(vacancy_id: int) -> Optional[Dict]:
    """
    Получает полную информацию о вакансии по её id
    """
    response = requests.get(f"{API_URL}/vacancies/{vacancy_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения данных о вакансии {vacancy_id}")
        return None
