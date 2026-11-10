"""Locust load test configuration for SarkarSetu AI API."""
import os
import random
import uuid
from locust import HttpUser, task, between, events


class SarkarSetuUser(HttpUser):
    """Simulated user for load testing."""
    
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = None
        self.refresh_token = None
        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        self.business_profile_id = None
    
    def on_start(self):
        """Register and login a new user."""
        self.register()
        self.login()
        self.create_business_profile()
    
    def register(self):
        """Register a new user."""
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.user_email,
                "full_name": "Load Test User",
                "password": "StrongPassword123!",
            },
        )
        if response.status_code == 201:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        else:
            print(f"Registration failed: {response.status_code} - {response.text}")
    
    def login(self):
        """Login to get fresh tokens."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.user_email,
                "password": "StrongPassword123!",
            },
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
    
    def create_business_profile(self):
        """Create a business profile."""
        if not self.access_token:
            return
        
        response = self.client.post(
            "/api/v1/businesses/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "business_name": "Load Test Business",
                "business_type": "Manufacturing",
                "industry": "Textiles",
                "state": "Maharashtra",
                "district": "Mumbai",
                "business_structure": "Private Limited",
                "business_stage": "Growth",
                "annual_turnover": 5000000,
                "employee_count": 25,
            },
        )
        if response.status_code == 201:
            self.business_profile_id = response.json()["id"]
    
    def auth_headers(self):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
    
    @task(10)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/api/v1/health")
    
    @task(5)
    def get_me(self):
        """Get current user info."""
        self.client.get("/api/v1/auth/me", headers=self.auth_headers())
    
    @task(5)
    def list_business_profiles(self):
        """List business profiles."""
        self.client.get("/api/v1/businesses/", headers=self.auth_headers())
    
    @task(3)
    def get_business_profile(self):
        """Get specific business profile."""
        if self.business_profile_id:
            self.client.get(
                f"/api/v1/businesses/{self.business_profile_id}",
                headers=self.auth_headers(),
            )
    
    @task(3)
    def eligibility_assessment(self):
        """Run eligibility assessment."""
        if self.business_profile_id:
            self.client.post(
                "/api/v1/eligibility/assess",
                headers=self.auth_headers(),
                json={
                    "business_profile_id": self.business_profile_id,
                    "scheme_name": "udyam_registration",
                    "registration_type": "udyam_registration",
                    "business_attributes": {
                        "business_type": "Manufacturing",
                        "industry": "Textiles",
                        "state": "Maharashtra",
                        "business_structure": "Private Limited",
                        "business_stage": "Growth",
                        "annual_turnover": "5000000",
                        "employee_count": "25",
                    },
                    "missing_information": [],
                },
            )
    
    @task(2)
    def knowledge_search(self):
        """Search knowledge base."""
        self.client.post(
            "/api/v1/knowledge/search",
            headers=self.auth_headers(),
            json={
                "query": "Udyam registration requirements",
                "limit": 5,
            },
        )
    
    @task(2)
    def get_recommendations(self):
        """Get scheme recommendations."""
        if self.business_profile_id:
            self.client.post(
                "/api/v1/recommendations/",
                headers=self.auth_headers(),
                json={
                    "business_profile_id": self.business_profile_id,
                },
            )
    
    @task(2)
    def list_roadmaps(self):
        """List roadmaps."""
        self.client.get("/api/v1/roadmaps/", headers=self.auth_headers())
    
    @task(1)
    def chat_message(self):
        """Send chat message."""
        self.client.post(
            "/api/v1/chat/message",
            headers=self.auth_headers(),
            json={
                "message": "What are the requirements for Udyam registration?",
                "business_profile_id": self.business_profile_id,
            },
        )
    
    @task(1)
    def start_workflow(self):
        """Start a workflow."""
        if self.business_profile_id:
            self.client.post(
                "/api/v1/workflows/",
                headers=self.auth_headers(),
                json={
                    "service_type": "udyam_registration",
                    "message": "I want to register for Udyam",
                    "business_profile_id": self.business_profile_id,
                },
            )


class AuthenticatedOnlyUser(HttpUser):
    """User that only tests authenticated endpoints after login."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        # Use a pre-created user or create one
        self.access_token = None
        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        self.register_and_login()
    
    def register_and_login(self):
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.user_email,
                "full_name": "Load Test User",
                "password": "StrongPassword123!",
            },
        )
        if response.status_code == 201:
            self.access_token = response.json()["access_token"]
    
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
    
    @task
    def health_check(self):
        self.client.get("/api/v1/health")
    
    @task
    def get_me(self):
        if self.access_token:
            self.client.get("/api/v1/auth/me", headers=self.auth_headers())


# Event hooks for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test stopped.")


if __name__ == "__main__":
    print("Run with: locust -f locustfile.py --host=http://localhost:8000")