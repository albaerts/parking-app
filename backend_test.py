#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Parking App
Tests all core functionality: Authentication, Parking Spots, Hardware Simulation, Sessions, and Payments
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Backend URL from frontend .env
BASE_URL = "http://localhost:8000/api"

class ParkingAppTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.user_token = None
        self.owner_token = None
        self.user_data = None
        self.owner_data = None
        self.parking_spot_id = None
        self.hardware_id = None
        self.parking_session_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        })
        
    def make_request(self, method, endpoint, data=None, headers=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, params=params, timeout=60)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, params=params, timeout=60)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=60)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def test_user_registration(self):
        """Test 1: User Registration System"""
        print("\n=== Testing User Registration ===")
        
        # Test regular user registration
        user_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": user_email,
            "name": "John Parker",
            "password": "securepass123",
            "role": "user"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        if response and response.status_code == 200:
            result = response.json()
            self.user_token = result.get("access_token")
            self.user_data = result.get("user")
            self.log_test("User Registration", True, f"User registered successfully: {self.user_data['email']}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("User Registration", False, f"Failed to register user: {error_msg}")
            
        # Test owner registration
        owner_email = f"owner_{uuid.uuid4().hex[:8]}@example.com"
        owner_data = {
            "email": owner_email,
            "name": "Sarah Owner",
            "password": "ownerpass123",
            "role": "owner"
        }
        
        response = self.make_request("POST", "/auth/register", owner_data)
        if response and response.status_code == 200:
            result = response.json()
            self.owner_token = result.get("access_token")
            self.owner_data = result.get("user")
            self.log_test("Owner Registration", True, f"Owner registered successfully: {self.owner_data['email']}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Owner Registration", False, f"Failed to register owner: {error_msg}")

    def test_user_login(self):
        """Test 2: User Login System"""
        print("\n=== Testing User Login ===")
        
        if not self.user_data or not self.owner_data:
            self.log_test("Login Test", False, "Cannot test login - registration failed")
            return
            
        # Test user login
        login_data = {
            "email": self.user_data["email"],
            "password": "securepass123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            if token:
                self.log_test("User Login", True, "User login successful with JWT token")
            else:
                self.log_test("User Login", False, "Login successful but no token received")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("User Login", False, f"User login failed: {error_msg}")
            
        # Test owner login
        login_data = {
            "email": self.owner_data["email"],
            "password": "ownerpass123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            if token:
                self.log_test("Owner Login", True, "Owner login successful with JWT token")
            else:
                self.log_test("Owner Login", False, "Login successful but no token received")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Owner Login", False, f"Owner login failed: {error_msg}")

    def test_parking_spot_management(self):
        """Test 3: Parking Spot Management"""
        print("\n=== Testing Parking Spot Management ===")
        
        if not self.owner_token:
            self.log_test("Parking Spot Creation", False, "Cannot test - no owner token")
            return
            
        headers = {"Authorization": f"Bearer {self.owner_token}"}
        
        # Create parking spot with very high hourly rate to ensure minimum payment quickly
        spot_data = {
            "name": "Downtown Parking Spot A1",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "address": "123 Main St, New York, NY 10001",
            "hourly_rate": 100.00  # Very high rate to ensure minimum payment amount quickly
        }
        
        response = self.make_request("POST", "/parking-spots", spot_data, headers)
        if response and response.status_code == 200:
            result = response.json()
            self.parking_spot_id = result.get("id")
            self.hardware_id = result.get("hardware_id")
            self.log_test("Parking Spot Creation", True, f"Spot created with ID: {self.parking_spot_id}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Parking Spot Creation", False, f"Failed to create spot: {error_msg}")
            return
            
        # List parking spots
        response = self.make_request("GET", "/parking-spots")
        if response and response.status_code == 200:
            spots = response.json()
            if isinstance(spots, list) and len(spots) > 0:
                self.log_test("Parking Spot Listing", True, f"Retrieved {len(spots)} parking spots")
            else:
                self.log_test("Parking Spot Listing", False, "No parking spots found")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Parking Spot Listing", False, f"Failed to list spots: {error_msg}")
            
        # Get specific parking spot
        if self.parking_spot_id:
            response = self.make_request("GET", f"/parking-spots/{self.parking_spot_id}")
            if response and response.status_code == 200:
                spot = response.json()
                if spot.get("id") == self.parking_spot_id:
                    self.log_test("Parking Spot Retrieval", True, f"Retrieved spot: {spot.get('name')}")
                else:
                    self.log_test("Parking Spot Retrieval", False, "Retrieved spot ID mismatch")
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                self.log_test("Parking Spot Retrieval", False, f"Failed to retrieve spot: {error_msg}")

    def test_hardware_simulation(self):
        """Test 4: Real-time Hardware Simulation"""
        print("\n=== Testing Hardware Simulation ===")
        
        if not self.hardware_id:
            self.log_test("Hardware Status Update", False, "Cannot test - no hardware ID")
            return
            
        # Test setting spot as occupied - using query parameter
        response = self.make_request("POST", f"/hardware/{self.hardware_id}/status?is_available=false")
        if response and response.status_code == 200:
            result = response.json()
            if result.get("status") == "updated":
                self.log_test("Hardware Status Update (Occupied)", True, "Successfully set spot as occupied")
            else:
                self.log_test("Hardware Status Update (Occupied)", False, "Unexpected response format")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Hardware Status Update (Occupied)", False, f"Failed to update status: {error_msg}")
            
        # Verify the status change
        response = self.make_request("GET", f"/parking-spots/{self.parking_spot_id}")
        if response and response.status_code == 200:
            spot = response.json()
            if not spot.get("is_available"):
                self.log_test("Hardware Status Verification", True, "Spot status correctly updated to occupied")
            else:
                self.log_test("Hardware Status Verification", False, "Spot status not updated")
        else:
            self.log_test("Hardware Status Verification", False, "Failed to verify status change")
            
        # Test setting spot as available again
        response = self.make_request("POST", f"/hardware/{self.hardware_id}/status?is_available=true")
        if response and response.status_code == 200:
            self.log_test("Hardware Status Update (Available)", True, "Successfully set spot as available")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Hardware Status Update (Available)", False, f"Failed to update status: {error_msg}")

    def test_parking_session_management(self):
        """Test 5: Parking Session Management"""
        print("\n=== Testing Parking Session Management ===")
        
        if not self.user_token or not self.parking_spot_id:
            self.log_test("Parking Session Start", False, "Cannot test - missing user token or spot ID")
            return
            
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Start parking session
        params = {"spot_id": self.parking_spot_id}
        response = self.make_request("POST", "/parking-sessions", None, headers, params)
        if response and response.status_code == 200:
            result = response.json()
            self.parking_session_id = result.get("id")
            self.log_test("Parking Session Start", True, f"Session started with ID: {self.parking_session_id}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Parking Session Start", False, f"Failed to start session: {error_msg}")
            return
            
        # Wait to simulate parking time and ensure minimum payment (need at least $0.50)
        print("Simulating parking time (20 seconds to ensure minimum payment of $0.50)...")
        time.sleep(20)  # At $100/hour, need 0.005 hours = 18 seconds minimum
        
        # End parking session
        response = self.make_request("POST", f"/parking-sessions/{self.parking_session_id}/end", None, headers)
        if response and response.status_code == 200:
            result = response.json()
            total_amount = result.get("total_amount")
            duration_hours = result.get("duration_hours")
            if total_amount is not None and duration_hours is not None:
                self.log_test("Parking Session End", True, f"Session ended. Duration: {duration_hours:.4f}h, Amount: ${total_amount:.2f}")
            else:
                self.log_test("Parking Session End", False, "Session ended but missing pricing data")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Parking Session End", False, f"Failed to end session: {error_msg}")
            
        # Get user sessions
        response = self.make_request("GET", "/parking-sessions", None, headers)
        if response and response.status_code == 200:
            sessions = response.json()
            if isinstance(sessions, list) and len(sessions) > 0:
                self.log_test("Parking Session Retrieval", True, f"Retrieved {len(sessions)} user sessions")
            else:
                self.log_test("Parking Session Retrieval", False, "No sessions found for user")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Parking Session Retrieval", False, f"Failed to retrieve sessions: {error_msg}")

    def test_stripe_payment_integration(self):
        """Test 6: Stripe Payment Integration"""
        print("\n=== Testing Stripe Payment Integration ===")
        
        if not self.user_token or not self.parking_session_id:
            self.log_test("Payment Checkout Creation", False, "Cannot test - missing user token or session ID")
            return
            
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Create checkout session
        params = {"session_id": self.parking_session_id}
        response = self.make_request("POST", "/payments/checkout", None, headers, params)
        if response and response.status_code == 200:
            result = response.json()
            checkout_url = result.get("checkout_url")
            stripe_session_id = result.get("session_id")
            if checkout_url and stripe_session_id:
                self.log_test("Payment Checkout Creation", True, f"Checkout session created: {stripe_session_id}")
                
                # Test payment status check
                response = self.make_request("GET", f"/payments/status/{stripe_session_id}", None, headers)
                if response and response.status_code == 200:
                    status_result = response.json()
                    payment_status = status_result.get("payment_status")
                    if payment_status:
                        self.log_test("Payment Status Check", True, f"Payment status retrieved: {payment_status}")
                    else:
                        self.log_test("Payment Status Check", False, "Payment status not found in response")
                else:
                    error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                    self.log_test("Payment Status Check", False, f"Failed to check payment status: {error_msg}")
            else:
                self.log_test("Payment Checkout Creation", False, "Checkout session created but missing URL or session ID")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Payment Checkout Creation", False, f"Failed to create checkout session: {error_msg}")

    def test_error_handling(self):
        """Test 7: Error Handling"""
        print("\n=== Testing Error Handling ===")
        
        # Test unauthorized access with shorter timeout
        try:
            response = requests.post(f"{self.base_url}/parking-spots", json={"name": "Test"}, timeout=10)
            if response and response.status_code == 403:  # Should be 403 Forbidden
                self.log_test("Unauthorized Access Handling", True, "Correctly rejected unauthorized request")
            else:
                self.log_test("Unauthorized Access Handling", False, f"Expected 403, got {response.status_code if response else 'No response'}")
        except Exception as e:
            self.log_test("Unauthorized Access Handling", False, f"Request failed: {str(e)}")
            
        # Test invalid parking spot ID with shorter timeout
        try:
            response = requests.get(f"{self.base_url}/parking-spots/invalid-id", timeout=10)
            if response and response.status_code == 404:
                self.log_test("Invalid Resource Handling", True, "Correctly handled invalid parking spot ID")
            else:
                self.log_test("Invalid Resource Handling", False, f"Expected 404, got {response.status_code if response else 'No response'}")
        except Exception as e:
            self.log_test("Invalid Resource Handling", False, f"Request failed: {str(e)}")
            
        # Test duplicate email registration with shorter timeout
        if self.user_data:
            duplicate_data = {
                "email": self.user_data["email"],
                "name": "Duplicate User",
                "password": "password123",
                "role": "user"
            }
            try:
                response = requests.post(f"{self.base_url}/auth/register", json=duplicate_data, timeout=10)
                if response and response.status_code == 400:
                    self.log_test("Duplicate Email Handling", True, "Correctly rejected duplicate email registration")
                else:
                    self.log_test("Duplicate Email Handling", False, f"Expected 400, got {response.status_code if response else 'No response'}")
            except Exception as e:
                self.log_test("Duplicate Email Handling", False, f"Request failed: {str(e)}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Parking App Backend Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in logical order
        self.test_user_registration()
        self.test_user_login()
        self.test_parking_spot_management()
        self.test_hardware_simulation()
        self.test_parking_session_management()
        self.test_stripe_payment_integration()
        self.test_error_handling()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            
        print(f"\nOverall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend is working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
            
        return passed == total

if __name__ == "__main__":
    tester = ParkingAppTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)