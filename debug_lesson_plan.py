import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@bhashaai.in"
ADMIN_PASSWORD = "AdminPassword123!"

async def debug_lesson():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Auth
        resp = await client.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        token = resp.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("Requesting Gujarati Lesson Plan...")
        payload = {
            "tool_type": "lesson_plan",
            "topic": "Photosynthesis",
            "subject": "Science",
            "grade_level": "8",
            "language": "gu"
        }
        resp = await client.post(f"{BASE_URL}/teaching-tools/generate", json=payload, headers=headers)
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(debug_lesson())
