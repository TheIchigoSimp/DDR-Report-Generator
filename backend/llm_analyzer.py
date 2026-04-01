import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert building inspection analyst. You will receive text from two PDF reports: an Inspection Report and a Thermal Imaging Report for the same property.
Your job is to analyze BOTH reports and produce a structured JSON output for a Detailed Diagnostic Report (DDR).
STRICT RULES:
1. Output ONLY valid JSON — no markdown, no explanation, no text before or after.
2. Follow the exact schema below.
3. NEVER invent or assume facts not present in the reports.
4. If information is missing, write "Not Available".
5. If the two reports conflict, flag the conflict in your observations.
6. Use simple, professional language — avoid unnecessary jargon.
7. The "image_hint" field should contain 2-4 keywords describing what an image for that observation would show (e.g. "crack north wall bedroom"). This helps us match extracted images later.
8. The "source_pages" field must list the exact page numbers (integers) from the reports where this observation's information was found. Use the "--- Page N ---" markers in the text to determine page numbers.
9. Be THOROUGH and DETAILED. Every field should be comprehensive. Short 1-sentence responses are unacceptable — provide professional-grade analysis with specific references to the report data.

REQUIRED JSON SCHEMA:
{
  "property_issue_summary": "A comprehensive 4-6 sentence overview of the property's condition. Include property type, age, inspection score, key problem areas, and overall structural health assessment based on both reports.",
  "observations": [
    {
      "area": "Specific location (e.g. 'Living Room - North Wall')",
      "observation": "Detailed 2-4 sentence description of the issue. Include what was found, its extent/severity, visible signs (stains, cracks, peeling, dampness), and how the thermal vs inspection findings correlate.",
      "image_hint": "2-4 keywords for image matching (e.g. 'crack wall north')",
      "source": "inspection | thermal | both",
      "source_pages": [3, 4]
    }
  ],
  "probable_root_cause": "A detailed 3-5 sentence analysis of the likely root cause(s). Explain the chain of causation — what likely failed, why, and how it led to the observed damage. Reference specific observations.",
  "severity_assessment": {
    "level": "Critical | High | Moderate | Low",
    "reasoning": "A 2-3 sentence explanation of why this severity level was chosen. Reference the number of affected areas, extent of damage, and potential consequences if left unaddressed."
  },
  "recommended_actions": [
    "Action 1 — Detailed action with priority (Immediate/Short-term/Long-term), specific steps, and estimated scope. E.g. 'IMMEDIATE: Engage a waterproofing contractor to inspect and repair the terrace membrane. Focus on areas directly above the hall and bedroom where moisture ingress is most severe.'"
  ],
  "additional_notes": "2-3 sentences covering additional context — property age concerns, maintenance history gaps, seasonal considerations, or recommendations for follow-up inspections.",
  "missing_or_unclear_info": [
    "List anything that was missing or unclear in either report"
  ]
}"""


def generate_ddr_structure(inspection_text: str, thermal_text: str) -> dict:
    max_chars = 4000

    if len(inspection_text) > max_chars:
        inspection_text = inspection_text[:max_chars] + "\n[... truncated for length]"

    if len(thermal_text) > max_chars:
        thermal_text = thermal_text[:max_chars] + "\n[... truncated for length]"

    user_message = f"""Analyze the following two reports and produce the DDR JSON:
        {inspection_text}
        === THERMAL REPORT ===
        {thermal_text}"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=4096,
            )
            raw = response.choices[0].message.content.strip()

            if raw.startswith("```json"):
                raw = raw[7:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            
            result = json.loads(raw)
            
            print(f"[llm_analyzer] Successfully parsed DDR JSON on attempt {attempt + 1}")
            return result
        except json.JSONDecodeError as e:
            print(f"[llm_analyzer] JSON parse error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                print("[llm_analyzer] Retrying...")
                continue
        except Exception as e:
            print(f"[llm_analyzer] API error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                continue
    
    print("[llm_analyzer] All retries failed.")
    return {
        "error": "Failed to generate DDR structure after multiple attempts.",
        "property_issue_summary": "Analysis could not be completed.",
        "observations": [],
        "probable_root_cause": "Not Available",
        "severity_assessment": {"level": "Not Available", "reasoning": "Analysis failed."},
        "recommended_actions": [],
        "additional_notes": "The LLM failed to produce valid JSON. Please try again.",
        "missing_or_unclear_info": ["Complete analysis unavailable due to processing error."]
    }

if __name__ == "__main__":
    
    test_inspection = "Property: Flat, 11 floors. Cracks observed on north wall of bedroom. Water stains on ceiling of bathroom. Score: 85.71%"
    
    test_thermal = "Thermal scan shows moisture ingress along north wall at 2nd floor level. Temperature differential of 3.2°C detected near bathroom ceiling."
    
    print("Sending to Groq LLM...")
    
    ddr = generate_ddr_structure(test_inspection, test_thermal)
    
    print(json.dumps(ddr, indent=2))