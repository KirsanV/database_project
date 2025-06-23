import time
from typing import Dict, List, Optional

import requests


class APIClient:
    """
    Взаимодействие с API hh
    """

    def __init__(self, base_url: str = "https://api.hh.ru") -> None:
        """
        Инициализация API
        """
        self.base_url: str = base_url

    def get_companies(self, ids: List[int]) -> List[Dict]:
        """
        Получает информацию о компаниях по списку их id
        """
        companies: List[Dict] = []
        for company_id in ids:
            response = requests.get(f"{self.base_url}/employers/{company_id}")
            if response.status_code == 200:
                companies.append(response.json())
            else:
                print(f"Ошибка получения данных о компании {company_id}: {response.status_code}")
            time.sleep(0.2)
        return companies

    def get_vacancies_for_company(
            self,
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
            response = requests.get(f"{self.base_url}/vacancies", params=params)
            if response.status_code == 200:
                data = response.json()
                vacancies.extend(data.get('items', []))
                if data.get('pages', 0) <= page + 1:
                    break
            else:
                print(f"Ошибка получения вакансий для компании {company_id}: {response.status_code}")
            time.sleep(0.2)
        return vacancies

    def get_vacancy_details(self, vacancy_id: int) -> Optional[Dict]:
        """
        Получает полную информацию о вакансии по её id
        """
        response = requests.get(f"{self.base_url}/vacancies/{vacancy_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка получения данных о вакансии {vacancy_id}: {response.status_code}")
            return None
