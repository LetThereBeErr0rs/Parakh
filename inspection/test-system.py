#!/usr/bin/env python3
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║          PARAKH FACT-CHECKING SYSTEM - AUTOMATED TEST SUITE              ║
# ║              Run this after starting with start-system.ps1               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

import json
import requests
import sys
import time
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    response_time: float = 0.0

class ParakhTester:
    def __init__(self, backend_url: str = "http://127.0.0.1:8000", timeout: int = 10):
        self.backend_url = backend_url.rstrip('/')
        self.timeout = timeout
        self.results: List[TestResult] = []
        
    def print_banner(self, text: str, color: str = "cyan"):
        """Print a formatted banner"""
        colors = {
            "cyan": "\033[96m",
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "gray": "\033[90m",
        }
        reset = "\033[0m"
        color_code = colors.get(color, "")
        print(f"\n{color_code}{'═' * 70}\n{text:^70}\n{'═' * 70}{reset}\n")
    
    def print_result(self, result: TestResult):
        """Print a test result"""
        status = "✓ PASS" if result.passed else "✗ FAIL"
        status_color = "\033[92m" if result.passed else "\033[91m"
        reset = "\033[0m"
        time_str = f" ({result.response_time*1000:.0f}ms)" if result.response_time > 0 else ""
        print(f"{status_color}{status}{reset} {result.name}{time_str}")
        if result.message:
            print(f"       → {result.message}")
    
    def test_connection(self) -> bool:
        """Test if backend is reachable"""
        self.print_banner("Testing Backend Connection", "cyan")
        try:
            start = time.time()
            resp = requests.get(f"{self.backend_url}/", timeout=self.timeout)
            elapsed = time.time() - start
            
            result = TestResult(
                name="Backend Connectivity",
                passed=resp.status_code == 200,
                message=f"Status: {resp.status_code}, Response: {resp.json()}",
                response_time=elapsed
            )
            self.results.append(result)
            self.print_result(result)
            return result.passed
        except requests.exceptions.ConnectionError:
            result = TestResult(
                name="Backend Connectivity",
                passed=False,
                message="Cannot connect to backend. Is it running on port 8000?"
            )
            self.results.append(result)
            self.print_result(result)
            return False
        except Exception as e:
            result = TestResult(
                name="Backend Connectivity",
                passed=False,
                message=f"Error: {str(e)}"
            )
            self.results.append(result)
            self.print_result(result)
            return False
    
    def test_health(self):
        """Test health endpoint"""
        self.print_banner("Testing Health Endpoint", "cyan")
        try:
            start = time.time()
            resp = requests.get(f"{self.backend_url}/health", timeout=self.timeout)
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                gemini_keys = data.get('gemini_api_keys_configured', 0)
                faiss_ready = data.get('faiss_index_exists', False)
                data_available = data.get('data_sources_available', False)
                
                message = (
                    f"Gemini Keys: {gemini_keys}, "
                    f"FAISS: {'✓' if faiss_ready else '✗'}, "
                    f"Data: {'✓' if data_available else '✗'}"
                )
                result = TestResult(
                    name="Health Check",
                    passed=True,
                    message=message,
                    response_time=elapsed
                )
            else:
                result = TestResult(
                    name="Health Check",
                    passed=False,
                    message=f"Status: {resp.status_code}"
                )
            
            self.results.append(result)
            self.print_result(result)
        except Exception as e:
            result = TestResult(
                name="Health Check",
                passed=False,
                message=f"Error: {str(e)}"
            )
            self.results.append(result)
            self.print_result(result)
    
    def test_verify_text(self, claim: str, expected_status: str = None) -> bool:
        """Test text verification endpoint"""
        try:
            start = time.time()
            payload = {"text": claim}
            resp = requests.post(
                f"{self.backend_url}/verify-text",
                json=payload,
                timeout=self.timeout
            )
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                status = data.get('status', 'Unknown')
                confidence = data.get('confidence', 0)
                has_response = bool(status)
                
                if expected_status and status == expected_status:
                    passed = True
                    message = f"Status: {status} (✓ expected), Confidence: {confidence}%"
                elif expected_status:
                    passed = False
                    message = f"Status: {status} (✗ expected: {expected_status})"
                else:
                    passed = has_response
                    message = f"Status: {status}, Confidence: {confidence}%"
                
                result = TestResult(
                    name=f"Verify Text: '{claim[:40]}...'",
                    passed=passed,
                    message=message,
                    response_time=elapsed
                )
            else:
                result = TestResult(
                    name=f"Verify Text: '{claim[:40]}...'",
                    passed=False,
                    message=f"HTTP {resp.status_code}: {resp.text[:100]}"
                )
            
            self.results.append(result)
            self.print_result(result)
            return result.passed
        except Exception as e:
            result = TestResult(
                name=f"Verify Text: '{claim[:40]}...'",
                passed=False,
                message=f"Error: {str(e)}"
            )
            self.results.append(result)
            self.print_result(result)
            return False
    
    def run_all_tests(self):
        """Run all test suites"""
        self.print_banner("PARAKH FACT-CHECKING SYSTEM - TEST SUITE", "cyan")
        print(f"🚀 Testing Backend: {self.backend_url}")
        print(f"⏱️  Timeout: {self.timeout} seconds\n")
        
        # Basic connectivity
        if not self.test_connection():
            print("\n❌ Cannot reach backend. Make sure it's running!")
            return
        
        # Health status
        self.test_health()
        
        # Verification tests
        self.print_banner("Testing Verification Endpoints", "cyan")
        
        test_cases = [
            ("The Earth orbits the Sun.", "Supported"),
            ("The Earth is flat.", "Refuted"),
            ("Water boils at 100 degrees Celsius.", "Supported"),
            ("Vaccines cause autism.", "Refuted"),
        ]
        
        passed_tests = 0
        for claim, expected in test_cases:
            if self.test_verify_text(claim, expected):
                passed_tests += 1
            time.sleep(0.5)  # Rate limit
        
        # Summary
        self.print_banner("TEST SUMMARY", "green" if passed_tests == len(test_cases) else "yellow")
        
        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r.passed)
        total_failed = total_tests - total_passed
        
        print(f"📊 Results: {total_passed}/{total_tests} tests passed\n")
        
        if total_failed > 0:
            print(f"❌ {total_failed} test(s) failed:")
            for result in self.results:
                if not result.passed:
                    print(f"   • {result.name}: {result.message}")
        else:
            print("✓ All tests passed! System is ready to use.")
        
        # Performance summary
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\n⚡ Average Response Time: {avg_time*1000:.0f}ms")
        
        return total_failed == 0

if __name__ == "__main__":
    # Allow backend URL to be passed as argument
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    tester = ParakhTester(backend_url)
    success = tester.run_all_tests()
    
    print("\n" + "═" * 70)
    sys.exit(0 if success else 1)
