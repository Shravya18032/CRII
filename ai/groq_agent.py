from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_region(row):
    prompt = f"""
    You are a climate risk analyst.

    STRICT RULES:
    - Use ONLY the provided data
    - Do NOT assume population, infrastructure, or external causes
    - If top risks differ by < 0.05 → say "no strong dominant risk"
    - Do NOT explain temperature or climate unless explicitly asked
    - Do NOT use generic phrases like "urbanization pressure"

    Data:
    Flood: {row['flood_norm']}
    Heat: {row['lst_norm']}
    Vegetation: {row['veg_norm']}
    Urban: {row['urban_norm']}
    Rainfall: {row['rainfall_norm']}
    CRII: {row['crii']}

    Task:
    1. Identify dominant risk ONLY if clearly higher
    2. Otherwise say "balanced multi-risk"
    3. Explain based only on values

    Output:
    Main Risk: ___
    Explanation: ___
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    

    return response.choices[0].message.content