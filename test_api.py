"""
Test script for MediAgent API endpoints.
Run this to test all functionalities.
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n" + "="*60)
    print("1. Testing Health Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_upload(pdf_path=None):
    """Test document upload."""
    print("\n" + "="*60)
    print("2. Testing Upload Endpoint")
    print("="*60)
    
    if not pdf_path:
        print("⚠️  No PDF file provided. Skipping upload test.")
        print("To test upload, run: test_upload('path/to/your/file.pdf')")
        return None
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return None
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json()
    return None


def test_query(question="What is this document about?", session_id="test-session"):
    """Test query endpoint."""
    print("\n" + "="*60)
    print("3. Testing Query Endpoint")
    print("="*60)
    
    payload = {
        "question": question,
        "session_id": session_id
    }
    
    print(f"Question: {question}")
    response = requests.post(
        f"{BASE_URL}/query",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"\nAnswer: {result.get('answer', 'No answer')}")
    print(f"Citations: {len(result.get('citations', []))} found")
    print(f"Grounding Score: {result.get('grounding_score', 0):.2f}")
    print(f"Tool Calls: {len(result.get('tool_calls', []))}")
    
    if result.get('citations'):
        print("\nCitations:")
        for i, citation in enumerate(result['citations'][:3], 1):
            print(f"  {i}. {citation}")
    
    return result


def test_audit(request_id):
    """Test audit endpoint."""
    print("\n" + "="*60)
    print("4. Testing Audit Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/audit/{request_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def run_full_test(pdf_path=None):
    """Run complete test suite."""
    print("\n" + "🧪 " + "="*56)
    print("  MediAgent API Test Suite")
    print("="*60 + "\n")
    
    # Test 1: Health Check
    health_ok = test_health()
    
    # Test 2: Upload (optional, requires PDF)
    upload_result = None
    if pdf_path:
        upload_result = test_upload(pdf_path)
    
    # Test 3: Query
    query_result = test_query(
        question="What are the key findings in the document?",
        session_id="test-session-001"
    )
    
    # Test 4: Audit (if we have a request_id from query)
    if query_result and 'request_id' in query_result:
        test_audit(query_result['request_id'])
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"✅ Health Check: {'PASSED' if health_ok else 'FAILED'}")
    print(f"{'✅' if upload_result else '⚠️ '} Upload: {'PASSED' if upload_result else 'SKIPPED (no PDF provided)'}")
    print(f"✅ Query: {'PASSED' if query_result else 'FAILED'}")
    print("\n💡 Tip: Visit http://localhost:8000/docs for interactive testing!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run tests
    # To test with a PDF, provide the path:
    # run_full_test("path/to/your/clinical_document.pdf")
    
    run_full_test()
    
    # Example: Test specific questions
    print("\n" + "="*60)
    print("🔬 Testing Different Question Types")
    print("="*60)
    
    test_questions = [
        "Summarize the main points of the document",
        "What medications are mentioned?",
        "Calculate 150 * 2.5",  # Tests calculator tool
        "What is the patient's diagnosis?",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i} ---")
        test_query(question, session_id=f"test-session-{i:03d}")
