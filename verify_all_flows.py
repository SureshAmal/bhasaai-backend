import asyncio
import httpx
import json
import logging
import os
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@bhashaai.in"
ADMIN_PASSWORD = "AdminPassword123!"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("verifier")

class FlowVerifier:
    def __init__(self):
        self.headers = {}
        self.client = httpx.AsyncClient(timeout=60.0)
        self.state = {} # To share IDs between steps

    async def log(self, message, success=None):
        if success is True:
            print(f"{GREEN}✅ {message}{RESET}")
        elif success is False:
            print(f"{RED}❌ {message}{RESET}")
        else:
            print(f"{CYAN}ℹ️  {message}{RESET}")

    async def close(self):
        await self.client.aclose()

    async def verify_auth(self):
        print(f"\n{BOLD}1. Authentication Flow{RESET}")
        resp = await self.client.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if resp.status_code == 200:
            data = resp.json()["data"]
            self.headers = {"Authorization": f"Bearer {data['tokens']['access_token']}"}
            user = data["user"]
            await self.log(f"Login Successful: {user['full_name']} ({user['role']['name']})", True)
            self.state["user_id"] = user["id"]
            return True
        else:
            await self.log(f"Login Failed: {resp.text}", False)
            return False

    async def verify_documents(self):
        print(f"\n{BOLD}2. Document Flow{RESET}")
        # Create dummy file
        filename = "test_doc.txt"
        with open(filename, "w") as f:
            f.write("Photosynthesis is the process by which green plants manufacture food using sunlight.")
            
        try:
            files = {"file": (filename, open(filename, "rb"), "text/plain")}
            resp = await self.client.post(f"{BASE_URL}/documents/upload", files=files, headers=self.headers)
            
            if resp.status_code == 201:
                doc = resp.json()["data"]
                self.state["document_id"] = doc["id"]
                await self.log(f"Document Uploaded: {doc['filename']} (ID: {doc['id']})", True)
                return True
            else:
                await self.log(f"Upload Failed: {resp.text}", False)
                return False
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    async def verify_question_paper(self):
        print(f"\n{BOLD}3. Question Paper Flow{RESET}")
        # Generate
        payload = {
            "title": "Full Flow Test Paper",
            "subject": "Science",
            "total_marks": 20,
            "context": "Basic physics concepts like Newton's laws.",
            "grade_level": "9",
            "language": "en",
            "question_types": {"short_answer": 2, "mcq": 2},
            "difficulty_distribution": {"medium": 100}
        }
        resp = await self.client.post(f"{BASE_URL}/question-papers/generate", json=payload, headers=self.headers)
        if resp.status_code == 201:
            qp = resp.json()["data"]
            self.state["qp_id"] = qp["id"]
            await self.log(f"QP Generated: {qp['title']} (ID: {qp['id']})", True)
            
            # Fetch details
            get_resp = await self.client.get(f"{BASE_URL}/question-papers/{qp['id']}", headers=self.headers)
            if get_resp.status_code == 200:
                full_qp = get_resp.json()["data"]
                self.state["questions"] = full_qp.get("questions", [])
                await self.log(f"Details Fetched: {len(self.state['questions'])} questions found", True)
                return True
            else:
                await self.log("Failed to fetch QP details", False)
                return False
        else:
            await self.log(f"QP Gen Failed: {resp.text}", False)
            return False

    async def verify_assignments(self):
        print(f"\n{BOLD}4. Assignment Flow{RESET}")
        if "qp_id" not in self.state:
            await self.log("Skipping (No QP ID)", False)
            return

        # Create Assignment
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        payload = {
            "title": "Physics Homework",
            "description": "Complete all questions.",
            "question_paper_id": self.state["qp_id"],
            "due_date": due_date,
            "status": "published"
        }
        resp = await self.client.post(f"{BASE_URL}/assignments", json=payload, headers=self.headers)
        if resp.status_code == 201:
            assign = resp.json()["data"]
            self.state["assignment_id"] = assign["id"]
            await self.log(f"Assignment Created: {assign.get('question_text', 'No Title')} (ID: {assign['id']})", True)
            return True
        else:
            await self.log(f"Assignment Creation Failed: {resp.text}", False)
            return False

    async def verify_teaching_tools(self):
        print(f"\n{BOLD}5. Teaching Tools Flow{RESET}")
        
        # A. Lesson Plan
        lp_payload = {
            "tool_type": "lesson_plan",
            "topic": "Gravitation",
            "subject": "Physics",
            "grade_level": "9",
            "language": "en"
        }
        resp = await self.client.post(f"{BASE_URL}/teaching-tools/generate", json=lp_payload, headers=self.headers)
        if resp.status_code == 201:
            await self.log("Lesson Plan Generated", True)
        else:
            await self.log(f"Lesson Plan Failed: {resp.text}", False)

        # B. Mind Map
        mm_payload = {
            "tool_type": "mind_map",
            "topic": "Ecosystem",
            "subject": "Biology", 
            "grade_level": "8",
            "language": "en"
        }
        resp = await self.client.post(f"{BASE_URL}/teaching-tools/generate", json=mm_payload, headers=self.headers)
        if resp.status_code == 201:
            data = resp.json()["data"]
            # Basic validation of mind map structure
            if "content" in data and "id" in data["content"]:
                await self.log("Mind Map Generated (Valid JSON structure)", True)
            else:
                await self.log("Mind Map Generated but invalid structure", False)
        else:
            await self.log(f"Mind Map Failed: {resp.text}", False)
            
        # C. Analogy
        an_payload = {
            "tool_type": "analogy",
            "topic": "Voltage and Current",
            "subject": "Physics",
            "grade_level": "10",
            "language": "en"
        }
        resp = await self.client.post(f"{BASE_URL}/teaching-tools/generate", json=an_payload, headers=self.headers)
        if resp.status_code == 201:
            await self.log("Analogy Generated", True)
        else:
             await self.log(f"Analogy Failed: {resp.text}", False)

    async def verify_paper_checking(self):
        print(f"\n{BOLD}6. Paper Checking Flow{RESET}")
        if "qp_id" not in self.state:
            await self.log("Skipping (No QP ID)", False)
            return

        # Create Answer Key
        key_payload = {
            "question_paper_id": self.state["qp_id"],
            "content": {"1": {"expected_answer": "Test Answer", "max_marks": 5}}
        }
        resp = await self.client.post(f"{BASE_URL}/paper-checking/answer-key", json=key_payload, headers=self.headers)
        if resp.status_code in [200, 201]:
             await self.log("Answer Key Created", True)
        else:
             await self.log(f"Answer Key Failed: {resp.text}", False)

    async def verify_learning(self):
        print(f"\n{BOLD}7. Learning Module Flow{RESET}")
        
        # Profile
        resp = await self.client.get(f"{BASE_URL}/learning/profile", headers=self.headers)
        if resp.status_code == 200:
            await self.log("Profile Fetched", True)
        else:
            await self.log(f"Profile Failed: {resp.text}", False)
            
        # Daily Vocab
        resp = await self.client.get(f"{BASE_URL}/learning/vocabulary/daily", headers=self.headers)
        if resp.status_code == 200:
            items = resp.json()["data"]
            await self.log(f"Daily Words Fetched ({len(items)} items)", True)
            
            # SM-2 Progress Update
            if items:
                word_id = items[0]["word"]["id"]
                prog_resp = await self.client.post(
                    f"{BASE_URL}/learning/vocabulary/{word_id}/progress",
                    json={"quality": 4},
                    headers=self.headers
                )
                if prog_resp.status_code == 200:
                    await self.log("Progress/SM-2 Algorithm Updated", True)
                else:
                    await self.log(f"Progress Update Failed: {prog_resp.text}", False)
        else:
            await self.log(f"Vocab Failed: {resp.text}", False)

    async def run(self):
        print(f"{BOLD}🎬 Starting Comprehensive System Verification{RESET}")
        
        if await self.verify_auth():
            await self.verify_documents()
            await self.verify_question_paper()
            await self.verify_assignments()
            await self.verify_teaching_tools()
            await self.verify_paper_checking()
            await self.verify_learning()
            
        await self.close()
        print(f"\n{BOLD}🏁 Verification Finished{RESET}")

if __name__ == "__main__":
    verifier = FlowVerifier()
    asyncio.run(verifier.run())
