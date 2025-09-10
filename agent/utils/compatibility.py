from django.http import JsonResponse
import requests

BASE_URL = "https://api.vedastro.org"
def compatibility_report(person1,person2):
    # Example – replace with user input
    try:
        response = requests.post(f"{BASE_URL}/GetMatch", json={'person1':person1,'person2':person2})
        print(response)
        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            return {"error": "Failed to fetch compatibility", "details": response.text}
    except Exception as e:
        return {"error":'Failed to fetch compatibility',"details":e}
