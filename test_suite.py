import os
import sys
import json
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app

class TestAIStudyBuddy(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_homepage(self):
        """Test that the homepage loads successfully with HTML content."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Study Buddy", response.data)
        self.assertIn(b"Concept Explainer", response.data)
        self.assertIn(b"Notes Generator", response.data)
        self.assertIn(b"AI Quiz", response.data)
        self.assertIn(b"Coding Assistant", response.data)
        print("✓ test_homepage: PASSED (200 OK, HTML loaded)")

    def test_api_status(self):
        """Test healthcheck and API status endpoint."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")
        self.assertIn("has_api_key", data)
        self.assertIn("sdk_mode", data)
        print(f"✓ test_api_status: PASSED (Status: online, Mode: {data['sdk_mode']})")

    def test_empty_inputs(self):
        """Test that all endpoints properly validate and reject empty inputs with 400 Bad Request."""
        endpoints = [
            ("/explain", {"topic": ""}),
            ("/notes", {"topic": ""}),
            ("/quiz", {"topic": ""}),
            ("/code", {"query": ""}),
        ]
        for url, payload in endpoints:
            resp = self.client.post(url, json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertIn("error", data)
        print("✓ test_empty_inputs: PASSED (All empty submissions return 400 with error feedback)")

    def test_endpoints_without_api_key(self):
        """Test that missing API keys return friendly 503 error feedback without crashing."""
        # If API key is not present or default dummy
        endpoints = [
            ("/explain", {"topic": "Photosynthesis"}),
            ("/notes", {"topic": "Object Oriented Programming"}),
            ("/quiz", {"topic": "Python"}),
            ("/code", {"query": "Explain recursion"}),
        ]
        for url, payload in endpoints:
            resp = self.client.post(url, json=payload)
            # Either 200 (if live API key configured) or 503 (if missing key)
            self.assertIn(resp.status_code, [200, 503])
            data = resp.get_json()
            if resp.status_code == 503:
                self.assertIn("error", data)
                self.assertIn("GEMINI_API_KEY", data["error"])
        print("✓ test_endpoints_without_api_key: PASSED (Endpoints handle unconfigured API keys cleanly)")

if __name__ == "__main__":
    unittest.main()
