import os
import json
from typing import Optional
import streamlit as st
import anthropic

MODEL = "claude-sonnet-5"

def _get_api_key() -> Optional[str]:
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")

def get_chart_recommendations(profile: dict, focus: str = "") -> Optional[dict]:
    api_key = _get_api_key()
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)

    focus_instruction = (
        f"\nThe user specifically wants the dashboard to focus on: {focus}\n"
        "Prioritize KPIs and charts relevant to this, while still using only "
        "columns that exist in the profile."
        if focus.strip() else ""
    )

    prompt = f"""You are a data analyst. Given this dataset profile, recommend:
1. Up to 4 KPI metrics worth highlighting as headline numbers
2. Up to 4 charts worth showing on a dashboard
3. A short 3-4 sentence summary of the most interesting patterns you can infer
{focus_instruction}
Dataset profile:
{json.dumps(profile, indent=2)}

Respond with ONLY valid JSON, no other text, in exactly this format:
{{
  "summary": "...",
  "kpis": [
    {{"label": "Total Revenue", "column": "column_name", "agg": "sum"}}
  ],
  "charts": [
    {{"type": "bar", "x": "column_name", "y": "column_name or null", "title": "..."}}
  ]
}}

Valid chart types are: bar, line, scatter, histogram.
Valid agg values are: sum, mean, count, max, min.
Only recommend columns that actually exist in the profile above.
For "count", column can be any column (it just counts rows)."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = None
        for block in response.content:
            if block.type == "text":
                text = block.text.strip()
                break

        if text is None:
            st.error("No text response found from Claude.")
            return None

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except Exception as e:
        st.error(f"AI analysis failed: {e}")
        return None

def answer_question(profile: dict, question: str) -> str:
    """Answers a free-text question about the dataset using its profile."""
    api_key = _get_api_key()
    if not api_key:
        return "API key not configured — see README for setup."

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a data analyst. Answer the user's question about this
dataset using only the profile below. Be concise (2-4 sentences). If the
profile doesn't contain enough information to answer confidently, say so
rather than guessing.

Dataset profile:
{json.dumps(profile, indent=2)}

Question: {question}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "text":
                return block.text.strip()
        return "No response received."

    except Exception as e:
        return f"Error: {e}"