# Basic sanity tests for the WinBuild Cloud API
import unittest
import requests

class TestAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def test_health(self):
        response = requests.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
