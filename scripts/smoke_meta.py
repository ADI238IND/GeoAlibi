"""Explicit paid smoke test. Run only after setting MODEL_API_KEY and checking Billing."""
import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


async def main():
    load_dotenv()
    key = os.getenv("MODEL_API_KEY")
    if not key:
        raise SystemExit("Set MODEL_API_KEY in .env first. No request was sent.")
    from geoalibi.store import Store
    Store(Path(os.getenv('GEOALIBI_DATA_DIR', '.geoalibi'))).reserve(.01, float(os.getenv('GEOALIBI_API_BUDGET_USD', '10')))
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post("https://api.meta.ai/v1/chat/completions", headers={"Authorization": "Bearer " + key}, json={
            "model": "muse-spark-1.3", "max_completion_tokens": 512, "messages": [{"role": "user", "content": "Reply with the single word ready."}]})
        if response.status_code != 200:
            raise SystemExit(f"HTTP {response.status_code}. Check model access, key, and Billing. Response body omitted to avoid logging private content.")
        value = response.json()
        if value['choices'][0].get('finish_reason') != 'stop' or not value['choices'][0]['message'].get('content'):
            raise SystemExit('API authenticated, but completion did not finish. No connectivity success claimed.')
        print("Muse Spark connectivity:", value["choices"][0]["message"]["content"])
        print("Usage:", value.get("usage", {}))


if __name__ == "__main__":
    asyncio.run(main())
