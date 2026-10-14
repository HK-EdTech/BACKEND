"""Opt-in real homework smoke test; no OCR demo assets or automatic paid calls.

Set RAW_HOMEWORK_LIVE=1, OPENROUTER_API_KEY and RAW_HOMEWORK_FIXTURES to a
JSON manifest containing paths grouped by submissions, question_images and
marking_scheme, plus optional extra_information. Paths are relative to the manifest.
Enable this test after implementing the replacement workflow.
"""
import json
import os
from pathlib import Path
import pytest
from ai_agents.raw_homework_processing.agent import RawHomeworkProcessingAgent
from common.images import ImageBundle, sniff_mime

@pytest.mark.asyncio
async def test_live_smoke():
    if os.getenv("RAW_HOMEWORK_LIVE") != "1":
        pytest.skip("Set RAW_HOMEWORK_LIVE=1 to enable paid smoke testing")
    if not os.getenv("OPENROUTER_API_KEY") or not os.getenv("RAW_HOMEWORK_FIXTURES"):
        pytest.skip("Provide OPENROUTER_API_KEY and RAW_HOMEWORK_FIXTURES")
    manifest = Path(os.environ["RAW_HOMEWORK_FIXTURES"])
    inputs = json.loads(manifest.read_text(encoding="utf-8"))
    bundle = ImageBundle()
    for role in ("submissions", "question_images", "marking_scheme"):
        for relative in inputs.get(role, []):
            path = manifest.parent / relative
            data = path.read_bytes()
            bundle.add(role, path.name, data, sniff_mime(data))
    assert bundle.ids_for_role("submissions"), "Provide real submission images"
    agent = RawHomeworkProcessingAgent(api_key=os.environ["OPENROUTER_API_KEY"])
    result = await agent.run(bundle, extra_information=inputs.get("extra_information"))
    assert isinstance(result, dict)
    # Add outcome assertions once the new graph's output contract is defined.
