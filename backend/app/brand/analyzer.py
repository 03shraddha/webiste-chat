import json

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)
    return _client


def analyze_brand_tone(pages: list[dict], site_name: str) -> dict:
    """
    Samples up to 5 pages of content and asks Claude to produce a brand profile.

    Returns dict with:
        formality_level: "formal" | "casual" | "technical" | "friendly"
        key_terms: list of brand-specific terms/product names
        writing_patterns: description of sentence structure and tone
        brand_voice_summary: 2-3 sentences for injection into chat system prompt
    """
    if not pages:
        return _default_profile(site_name)

    sample_pages = pages[:5]
    samples = []
    for p in sample_pages:
        snippet = (p.get("content") or "")[:800].strip()
        title = p.get("title", "")
        if snippet:
            samples.append(f"--- Page: {title} ---\n{snippet}")

    if not samples:
        return _default_profile(site_name)

    combined_sample = "\n\n".join(samples)

    prompt = f"""Analyze the following website content samples from "{site_name}" and extract a brand voice profile.

CONTENT SAMPLES:
{combined_sample}

Return a JSON object with EXACTLY these fields:
{{
  "formality_level": "formal|casual|technical|friendly",
  "key_terms": ["list", "of", "brand-specific", "terms", "or", "product", "names"],
  "writing_patterns": "Brief description of sentence structure, tone markers, and style",
  "brand_voice_summary": "2-3 sentences describing how to write in this brand's voice. Be specific about tone, vocabulary, and style."
}}

Return ONLY valid JSON with no explanation or markdown formatting."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=settings.xai_model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        profile = json.loads(text)
        return profile
    except Exception as e:
        print(f"[BRAND] Analysis failed: {e}. Using default profile.")
        return _default_profile(site_name)


def _default_profile(site_name: str) -> dict:
    return {
        "formality_level": "professional",
        "key_terms": [],
        "writing_patterns": "Clear, informative sentences with a professional tone.",
        "brand_voice_summary": (
            f"Answer questions about {site_name} in a helpful, professional tone. "
            "Be concise, accurate, and friendly. Use clear language that matches the site's style."
        ),
    }
