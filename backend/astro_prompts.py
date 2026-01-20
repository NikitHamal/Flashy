"""
Astro Agent System Prompts

This module contains the system prompts and templates for the Flashy Astro agent.
The agent embodies a professional, experienced Vedic astrologer who is:
- Blunt, honest, and unfiltered
- Truth-speaking with divine insight
- Expert in classical Jyotish texts
- Precise in calculations and interpretations
"""

ASTRO_SYSTEM_PROMPT = """You are Flashy Astro, a professional Vedic astrologer with decades of experience studying and practicing Jyotish (Vedic Astrology). You have mastered the classical texts including Brihat Parashara Hora Shastra, Phaladeepika, Saravali, and Jataka Parijata.

Your personality:
- You are BLUNT and HONEST - you tell the truth without sugarcoating
- You are RAW and UNFILTERED - you speak directly about what you see in the charts
- You have DIVINE INSIGHT - you read charts with the eyes of Veda, seeing karma and destiny
- You are EXPERIENCED - you've seen thousands of charts and know patterns deeply
- You are PRECISE - your calculations and predictions are based on exact positions
- You are COMPASSIONATE but NOT SOFT - you deliver difficult truths with understanding

Your expertise includes:
- Birth chart (Rasi) analysis with all 12 houses
- Divisional charts (D9 Navamsha, D10 Dasamsha, etc.)
- Vimshottari and other Dasha systems
- Yoga identification (Raja, Dhana, Mahapurusha, Arishta yogas)
- Transit analysis (Gochar)
- Compatibility matching (Kundali Milan)
- Muhurta (auspicious timing)
- Remedial measures (mantras, gemstones, rituals)

Current Context:
- Number of stored kundalis: {kundali_count}
- Ayanamsa system: Lahiri (Chitrapaksha)

IMPORTANT GUIDELINES:

1. ALWAYS use tools to get actual chart data before making interpretations. Never guess positions.

2. When a user provides birth details, FIRST create their kundali using the create_kundali tool, THEN analyze it.

3. If the user asks about astrology without providing birth details, ask for:
   - Full name
   - Birth date (DD-MM-YYYY or similar)
   - Birth time (as precise as possible)
   - Birth place (city/town for coordinates)
   - Gender

4. When interpreting charts, always consider:
   - Lagna (Ascendant) and Lagna lord placement
   - Moon sign and Nakshatra (for mind and emotions)
   - Relevant house lords and their placements
   - Current Dasha/Antardasha periods
   - Key yogas present in the chart

5. Be SPECIFIC in your interpretations. Don't give generic readings. Reference exact positions.

6. When users ask general astrology questions, you can educate them, but for personal readings, insist on accurate birth data.

7. NEVER fabricate chart positions or dasha periods. If you don't have the data, use the tools.

8. For predictions, always consider:
   - Current Mahadasha and Antardasha lords
   - Major transits (Saturn, Jupiter, Rahu-Ketu)
   - Relevant house activations

9. Speak with AUTHORITY. You are not guessing - you are reading the cosmic blueprint.

10. Use proper Vedic terminology (Rasi, Bhava, Graha, Nakshatra, Dasha) but explain when needed.

Available Tools:
{tools_description}

When you need to call a tool, use this JSON format:
```json
{{"action": "tool_name", "args": {{"param1": "value1", "param2": "value2"}}}}
```

REMEMBER: You are not just an astrologer - you are a truth-teller. The stars don't lie, and neither do you. Every chart tells a story of karma and potential. Read it with wisdom, deliver it with honesty."""


ASTRO_TOOL_RESULT_TEMPLATE = """
<tool_result tool="{tool_name}">
{output}
</tool_result>

Continue with your analysis based on this data. Be specific and reference the actual positions shown above."""


def get_system_prompt(kundali_count: int = 0, tools: list = None) -> str:
    """Generate the system prompt with current context."""
    tools_desc = ""
    if tools:
        for tool in tools:
            tools_desc += f"\n- {tool['name']}: {tool['description']}"
            if tool.get('required'):
                tools_desc += f"\n  Required: {', '.join(tool['required'])}"
    
    return ASTRO_SYSTEM_PROMPT.format(
        kundali_count=kundali_count,
        tools_description=tools_desc or "(Tools will be provided)"
    )


# Interpretation Templates

PLANET_INTERPRETATION_TEMPLATE = """
{planet} Analysis:
Position: {sign} at {degree}° in {nakshatra} Nakshatra, Pada {pada}
House: {house} (Bhava {house})
Dignity: {dignity}
{retrograde_status}

Interpretation:
{interpretation}

Key Significations Affected:
{significations}
"""

DASHA_INTERPRETATION_TEMPLATE = """
Current Period Analysis:

Mahadasha: {mahadasha_lord}
- Duration: {md_start} to {md_end}
- Nature: {md_nature}
- Key themes: {md_themes}

Antardasha: {antardasha_lord}
- Duration: {ad_start} to {ad_end}
- Combined effect: {combined_effect}

What to Expect:
{predictions}

Recommendations:
{recommendations}
"""

YOGA_INTERPRETATION_TEMPLATE = """
{yoga_name}
Category: {category}
Strength: {strength}%

Formation:
{formation}

Effects in Your Life:
{effects}

Activation Periods:
{activation}

{remedies_section}
"""

COMPATIBILITY_TEMPLATE = """
Compatibility Analysis

Partner 1: {name1}
- Moon Sign: {moon1}
- Nakshatra: {nak1}

Partner 2: {name2}
- Moon Sign: {moon2}
- Nakshatra: {nak2}

Ashtakoota Score: {total_score}/36

Detailed Analysis:
{koota_analysis}

Relationship Dynamics:
{dynamics}

Challenges to Address:
{challenges}

Remedies for Harmony:
{remedies}
"""


# Common Interpretations Database

HOUSE_LORD_INTERPRETATIONS = {
    1: {
        "good": "Strong sense of self, good health, natural leadership",
        "bad": "Identity issues, health concerns, difficulty asserting oneself"
    },
    2: {
        "good": "Wealth accumulation, strong family bonds, sweet speech",
        "bad": "Financial struggles, family conflicts, speech issues"
    },
    3: {
        "good": "Courageous, good communication, supportive siblings",
        "bad": "Lack of initiative, sibling conflicts, short journey troubles"
    },
    4: {
        "good": "Domestic happiness, property gains, mother's blessings",
        "bad": "Mental unrest, property issues, maternal concerns"
    },
    5: {
        "good": "Creative talents, blessed with children, speculative gains",
        "bad": "Progeny concerns, creative blocks, poor judgment"
    },
    6: {
        "good": "Victory over enemies, good health, service success",
        "bad": "Health issues, debt, conflicts with subordinates"
    },
    7: {
        "good": "Happy marriage, successful partnerships, public recognition",
        "bad": "Relationship struggles, business partnership issues"
    },
    8: {
        "good": "Research abilities, inheritance, occult knowledge, longevity",
        "bad": "Sudden upheavals, health emergencies, hidden enemies"
    },
    9: {
        "good": "Fortune, spiritual growth, father's blessings, higher learning",
        "bad": "Luck delays, spiritual confusion, father-related issues"
    },
    10: {
        "good": "Career success, recognition, authority positions",
        "bad": "Professional setbacks, reputation issues, authority conflicts"
    },
    11: {
        "good": "Gains, fulfilled desires, supportive friends, elder sibling help",
        "bad": "Unfulfilled wishes, friend betrayals, income instability"
    },
    12: {
        "good": "Spiritual liberation, foreign success, good sleep, charity",
        "bad": "Losses, isolation, hidden expenses, sleep issues"
    }
}

PLANET_NATURE = {
    "Sun": {"nature": "Malefic", "element": "Fire", "represents": "Soul, Authority, Father"},
    "Moon": {"nature": "Benefic", "element": "Water", "represents": "Mind, Mother, Emotions"},
    "Mars": {"nature": "Malefic", "element": "Fire", "represents": "Energy, Courage, Siblings"},
    "Mercury": {"nature": "Neutral", "element": "Earth", "represents": "Intelligence, Communication"},
    "Jupiter": {"nature": "Benefic", "element": "Ether", "represents": "Wisdom, Fortune, Children"},
    "Venus": {"nature": "Benefic", "element": "Water", "represents": "Love, Luxury, Spouse"},
    "Saturn": {"nature": "Malefic", "element": "Air", "represents": "Karma, Discipline, Delays"},
    "Rahu": {"nature": "Malefic", "element": "Air", "represents": "Obsession, Foreign, Illusion"},
    "Ketu": {"nature": "Malefic", "element": "Fire", "represents": "Liberation, Past Karma, Detachment"}
}


DIGNITY_EFFECTS = {
    "exalted": "This planet is at its strongest, giving maximum positive results of its significations.",
    "moolatrikona": "Nearly as strong as exaltation, the planet operates with great power and clarity.",
    "own": "The planet is comfortable and gives good results, operating at its natural capacity.",
    "neutral": "The planet gives results according to aspects, conjunctions, and house placement.",
    "debilitated": "The planet is weakened and may give delayed or diminished results. Remedies recommended."
}


def get_brief_reading(chart_data: dict) -> str:
    """Generate a brief reading summary."""
    return f"""Your Chart at a Glance:

Ascendant (Lagna): {chart_data.get('lagna', 'Unknown')}
This shapes your physical appearance, personality, and how the world perceives you.

Moon Sign: {chart_data.get('moon_sign', 'Unknown')}
This governs your mind, emotions, and mental patterns.

Sun Sign: {chart_data.get('sun_sign', 'Unknown')}
This represents your soul, vitality, and life purpose.

Current Dasha: {chart_data.get('current_dasha', 'Calculate for specifics')}
This planetary period colors your current life experiences."""
