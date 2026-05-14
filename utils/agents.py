"""
Claude-powered research agents for extracting investment team members
and building enriched profiles via web search.
"""

import anthropic
import json
import concurrent.futures
import re
from typing import Optional


def get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


# ── AGENT 1: Extract investment team members from scraped page text ──────────

EXTRACTION_SYSTEM = """You are an expert at reading investment plan and pension fund documents.
Your job is to extract the names and titles of people on the investment team, investment committee, 
or board of trustees from raw webpage text.

Return ONLY valid JSON — no markdown, no explanation, no backticks.

Format:
{
  "organization": "Name of the fund or plan",
  "team_members": [
    {
      "name": "Full Name",
      "title": "Job title or role",
      "bio_snippet": "Any bio text found on the page (1-2 sentences max, empty string if none)"
    }
  ],
  "confidence": "high|medium|low",
  "notes": "Any caveats about the extraction"
}

Rules:
- Only include real people with names, not generic roles without names
- Include investment committee members, CIO, portfolio managers, trustees with names
- Do NOT include board members who are purely governance/political unless they sit on investment committee
- If you find no investment team members, return an empty team_members array
"""


def extract_team_members(raw_text: str, source_url: str, api_key: str) -> dict:
    """
    Agent 1: Use Claude to extract investment team members from raw page text.
    Returns structured dict with team members list.
    """
    client = get_client(api_key)

    prompt = f"""Extract the investment team members from this webpage content.

Source URL: {source_url}

Page content:
{raw_text}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=EXTRACTION_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "organization": "Unknown",
            "team_members": [],
            "confidence": "low",
            "notes": f"JSON parse error. Raw response: {raw[:200]}"
        }


# ── AGENT 2: Research individual using web search ────────────────────────────

RESEARCH_SYSTEM = """You are a financial industry research analyst. Your job is to research 
investment professionals and write a concise, useful profile.

You will be given a person's name, title, and organization. Use your web search tool to find 
current information about them.

Focus on:
1. Current role and responsibilities  
2. Career background and prior positions
3. Educational background (if findable)
4. Investment philosophy or areas of focus
5. Any notable achievements, quotes, or public statements
6. LinkedIn URL if findable

Write a professional profile of 150-250 words. Be factual — only include what you can verify.
If you cannot find information, say so clearly rather than hallucinating details.

End your response with a JSON block in this exact format (inside <json> tags):
<json>
{
  "linkedin_url": "URL or empty string",
  "key_facts": ["fact 1", "fact 2", "fact 3"],
  "confidence": "high|medium|low",
  "search_notes": "brief note on what you found/didn't find"
}
</json>
"""


def research_person(name: str, title: str, organization: str, source_url: str, api_key: str) -> dict:
    """
    Agent 2: Research a single investment professional using Claude + web search.
    Returns enriched profile dict.
    """
    client = get_client(api_key)

    prompt = f"""Please research this investment professional:

Name: {name}
Title: {title}
Organization: {organization}
Source: {source_url}

Search for their background, career history, and any public information about their work.
Write a professional profile and include the JSON metadata block at the end."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=RESEARCH_SYSTEM,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )

        # Collect all text blocks from response
        full_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_text += block.text

        # Extract JSON metadata
        json_match = re.search(r"<json>(.*?)</json>", full_text, re.DOTALL)
        metadata = {}
        if json_match:
            try:
                metadata = json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                metadata = {}

        # Clean profile text (remove the json block)
        profile_text = re.sub(r"<json>.*?</json>", "", full_text, flags=re.DOTALL).strip()

        return {
            "name": name,
            "title": title,
            "organization": organization,
            "source_url": source_url,
            "ai_profile": profile_text,
            "linkedin_url": metadata.get("linkedin_url", ""),
            "key_facts": metadata.get("key_facts", []),
            "confidence": metadata.get("confidence", "medium"),
            "search_notes": metadata.get("search_notes", ""),
        }

    except Exception as e:
        return {
            "name": name,
            "title": title,
            "organization": organization,
            "source_url": source_url,
            "ai_profile": "Research unavailable - please retry",
            "linkedin_url": "",
            "key_facts": [],
            "confidence": "low",
            "search_notes": str(e),
        }


def research_team_parallel(
    team_members: list[dict],
    organization: str,
    source_url: str,
    api_key: str,
    max_workers: int = 3,
    progress_callback=None,
) -> list[dict]:
    """
    Spin up parallel research agents for each team member.
    max_workers controls concurrency (keep low to avoid rate limits).
    progress_callback(name, index, total) called after each person finishes.
    """
    results = []
    total = len(team_members)

    def research_one(args):
        idx, member = args
        result = research_person(
            name=member["name"],
            title=member.get("title", ""),
            organization=organization,
            source_url=source_url,
            api_key=api_key,
        )
        result["baseline_bio"] = member.get("bio_snippet", "")
        if progress_callback:
            progress_callback(member["name"], idx + 1, total)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(research_one, (i, m)): i for i, m in enumerate(team_members)}
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            member = team_members[idx]
            try:
                results.append(future.result())
            except Exception as e:
                results.append({
                    "name": member["name"],
                    "title": member.get("title", ""),
                    "organization": organization,
                    "source_url": source_url,
                    "ai_profile": "Research unavailable - please retry",
                    "linkedin_url": "",
                    "key_facts": [],
                    "confidence": "low",
                    "search_notes": str(e),
                })

    return results
