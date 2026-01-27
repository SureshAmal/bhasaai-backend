import asyncio
import httpx
import json
import logging
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@bhashaai.in"
ADMIN_PASSWORD = "AdminPassword123!"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("verifier")

async def test_feature(name: str, coro):
    try:
        print(f"\n{BOLD}Testing {name}...{RESET}")
        await coro
        print(f"{GREEN}✅ {name} Passed{RESET}")
        return True
    except Exception as e:
        print(f"{RED}❌ {name} Failed: {e}{RESET}")
        return False

async def verify_auth(client):
    response = await client.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    data = response.json()["data"]
    token = data["tokens"]["access_token"]
    user = data["user"]
    print(f"  User: {user['full_name']} ({user['role']['name']})")
    return token

async def verify_question_paper(client, headers):
    # Generate English Paper
    payload = {
        "title": "Feature Test QP",
        "subject": "Mathematics",
        "total_marks": 20,
        "context": "Pythagoras theorem and basic geometry.",
        "grade_level": "10",
        "language": "en",
        "question_types": {"short_answer": 2},
        "difficulty_distribution": {"medium": 100, "easy": 0, "hard": 0}
    }
    resp = await client.post(f"{BASE_URL}/question-papers/generate", json=payload, headers=headers)
    if resp.status_code != 201:
        raise Exception(f"QP Gen failed: {resp.text}")
    
    qp = resp.json()["data"]
    print(f"  Generated QP ID: {qp['id']}")
    
    # Verify Questions exist
    resp = await client.get(f"{BASE_URL}/question-papers/{qp['id']}", headers=headers)
    full_qp = resp.json()["data"]
    questions = full_qp.get("questions", [])
    if not questions:
        raise Exception("No questions found in generated paper")
    print(f"  Questions generated: {len(questions)}")
    return qp['id']

async def verify_teaching_tools(client, headers):
    # Generate Gujarati Lesson Plan
    payload = {
        "tool_type": "lesson_plan",
        "topic": "Human Digestive System",
        "subject": "Biology",
        "grade_level": "8",
        "language": "gu"
    }
    resp = await client.post(f"{BASE_URL}/teaching-tools/generate", json=payload, headers=headers)
    if resp.status_code != 201:
        raise Exception(f"Tool Gen failed: {resp.text}")
    
    tool = resp.json()["data"]
    content = tool["content"]
    
    # Check for Gujarati characters
    import re
    if not re.search(r'[\u0A80-\u0AFF]', json.dumps(content)):
         print(f"  {RED}Warning: Content might missing Gujarati characters{RESET}")
    else:
         print(f"  Verified Gujarati content present")
         
    print(f"  Lesson Plan: {tool['topic']}")

async def verify_learning_module(client, headers):
    # 1. Profile
    resp = await client.get(f"{BASE_URL}/learning/profile", headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Profile fetch failed: {resp.text}")
    profile = resp.json()["data"]
    print(f"  XP: {profile['total_xp']}, Streak: {profile['streak_days']} days")
    
    # 2. Daily Vocab
    resp = await client.get(f"{BASE_URL}/learning/vocabulary/daily", headers=headers)
    if resp.status_code != 200:
         raise Exception(f"Vocab fetch failed: {resp.text}")
    vocab = resp.json()["data"]
    print(f"  Daily Words: {len(vocab)}")
    
    # 3. TTS
    tts_resp = await client.post(f"{BASE_URL}/learning/audio/tts", json={
        "text": "કેમ છો", "language": "gu"
    }, headers=headers)
    if tts_resp.status_code == 200:
        print("  TTS Audio generated successfully")
    else:
        print(f"  {RED}TTS Failed (Optional): {tts_resp.text}{RESET}")

async def verify_paper_checking(client, headers, qp_id):
    # Create Answer Key first
    key_payload = {
        "question_paper_id": qp_id,
        "content": {"1": {"expected_answer": "a^2 + b^2 = c^2", "max_marks": 5}}
    }
    resp = await client.post(f"{BASE_URL}/paper-checking/answer-key", json=key_payload, headers=headers)
    if resp.status_code not in [200, 201]:
        raise Exception(f"Answer Key creation failed: {resp.text}")
    print("  Answer Key created")
    
    # Note: Full submission requires file upload (mocking might be complex here without a real file)
    # We will skip submission checking in this script to keep it simple, 
    # as it requires an image file.
    print("  (Skipping Submission Upload - requires multipart file)")

async def main():
    print(f"{BOLD}🎬 Starting BhashaAI Feature Verification{RESET}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Auth
        try:
            token = await verify_auth(client)
            headers = {"Authorization": f"Bearer {token}"}
            print(f"{GREEN}✅ Auth Passed{RESET}")
        except Exception as e:
            print(f"{RED}❌ Auth Failed: {e}{RESET}")
            return

        # 2. Question Paper
        qp_id = None
        if await test_feature("AI Question Paper Generator", verify_question_paper(client, headers)):
            # We need qp_id for paper checking, but test_feature swallows return.
            # Rerunning logic or just grabbing it is cleaner.
            # Let's just re-run or rely on variable passing. 
            # Ideally valid testing struct.
            pass
            
        # Re-get QP ID properly
        # (For simplicity in this script, just re-running the generation code block essentially or 
        # I'll just refactor verify_question_paper to set a global or return val handling)
        # Refactoring main loop for better flow:
        
        try:
            print(f"\n{BOLD}Testing AI Question Paper Generator...{RESET}")
            qp_id = await verify_question_paper(client, headers)
            print(f"{GREEN}✅ AI Question Paper Generator Passed{RESET}")
        except Exception as e:
            print(f"{RED}❌ AI Question Paper Generator Failed: {e}{RESET}")

        # 3. Teaching Tools
        await test_feature("Teaching Tools (Gujarati Lesson Plan)", verify_teaching_tools(client, headers))

        # 4. Learning Module
        await test_feature("Gujarati Learning Module", verify_learning_module(client, headers))
        
        # 5. Paper Checking Configuration
        if qp_id:
             await test_feature("Paper Checking (Answer Key)", verify_paper_checking(client, headers, qp_id))

    print(f"\n{BOLD}🏁 Verification Complete{RESET}")

if __name__ == "__main__":
    asyncio.run(main())
