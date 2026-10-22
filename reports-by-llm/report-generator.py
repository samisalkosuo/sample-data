import os
import random
import uuid
from datetime import datetime, timedelta
import time
import json
import requests
import argparse
import sys

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

REPORT_TYPE_DOCTOR_VISIT = "doctor_visit"
REPORT_TYPE_TRAFFIC_INCIDENT = "traffic_incident"
REPORT_TYPE_BUILDING_INSPECTION = "building_inspection"
REPORT_TYPE_PROJECT_UPDATE = "project_update"
REPORT_TYPE_SOCIAL_SERVICES_VISIT = "social_services_visit"

# Define available report types
AVAILABLE_REPORT_TYPES = [
    REPORT_TYPE_DOCTOR_VISIT,
    REPORT_TYPE_TRAFFIC_INCIDENT,
    REPORT_TYPE_BUILDING_INSPECTION,
    REPORT_TYPE_PROJECT_UPDATE,
    REPORT_TYPE_SOCIAL_SERVICES_VISIT,
]

# Prompt templates — copied verbatim from exported_report_prompts.md.
# Variables are filled via str.format_map(request_json).
PROMPT_TEMPLATES = {
    REPORT_TYPE_PROJECT_UPDATE: (
        "Write a Quarterly Project Update Report for a large-scale project titled {project_name} in the {industry} industry. "
        "The report covers {quarter}, and the project is currently in the {project_stage}.\n\n"
        "Begin the report by generating a realistic, fictional company name appropriate for the {industry} sector. "
        "Use this company name consistently throughout the report as the organization responsible for the project.\n\n"
        "The report must include:\n\n"
        "    Executive Summary – Overall project status, key progress points, and general sentiment (on track, behind, ahead).\n\n"
        "    Key Milestones Achieved – Completed deliverables, percentage of completion, and impact on company goals.\n\n"
        "    Current Risks and Blockers – Include challenges such as {primary_blocker}, and how they are being managed.\n\n"
        "    Next Quarter Objectives – Specific and realistic goals, including deliverables and timelines.\n\n"
        "    Resource and Budget Overview – Commentary on budget usage, staffing, vendor collaboration, and dependencies.\n\n"
        "Use a professional and structured tone suitable for senior stakeholders. "
        "Ensure the content is realistic and consistent with the project stage, blocker, and industry. "
        "Avoid generic or placeholder text."
    ),

    REPORT_TYPE_SOCIAL_SERVICES_VISIT: (
        "Write a Social Services Visit Report based on the following details:\n\n"
        "    Visit date: {date}\n\n"
        "    Location: {municipality}, {country}\n\n"
        "    Visit type: {visit_type}\n\n"
        "    Household composition: {household_composition}\n\n"
        "    Case severity: {case_severity}\n\n"
        "The report must include:\n\n"
        "    Summary of Visit Purpose – Why the visit was conducted, based on visit type and case context.\n\n"
        "    Observations During the Visit – Interactions, living conditions, behaviors, emotional state, or notable concerns.\n\n"
        "    Assessment – Evaluation of the situation, risks, and family dynamics in light of the case severity.\n\n"
        "    Recommended Actions or Follow-up – Next steps, referrals, support services, or timelines for further visits.\n\n"
        "Generate a realistic client name and address appropriate to the location, and maintain a professional, factual tone throughout. "
        "The report should be self-contained, free of placeholders, and contextually consistent with all given parameters. "
        "Avoid repetition and vary narrative structure between runs."
    ),

    REPORT_TYPE_DOCTOR_VISIT: (
        "You are a professional medical assistant generating a realistic and medically accurate doctor's visit report "
        "(visit summary) based on provided parameters.\n\n"
        "Generate a complete report that includes the following:\n\n"
        "    Visit Date: {date}\n\n"
        "    Clinic or Hospital Location: {location}\n\n"
        "    Severity Level: {severity}\n"
        "    (1 = Resuscitation – immediate life threat,\n"
        "    2 = Emergent – potential life threat,\n"
        "    3 = Urgent – stable, needs 2+ resources,\n"
        "    4 = Less-urgent – stable, 1 resource,\n"
        "    5 = Non-urgent – minor complaints)\n\n"
        "    Patient Gender: {patient_gender}\n\n"
        "    Patient Age: {patient_age}\n\n"
        "Required Output Format:\n\n"
        "Write a realistic visit summary that includes the following sections:\n\n"
        "    Chief Complaint – Patient's main reason for visit\n\n"
        "    History of Present Illness (HPI) – Detailed description of symptoms and onset\n\n"
        "    Physical Examination Findings – Based on severity and patient profile\n\n"
        "    Assessment / Diagnosis – Medical evaluation based on findings\n\n"
        "    Plan / Treatment – Medications, procedures, or recommendations\n\n"
        "    Follow-up Instructions – When and how to follow up\n\n"
        "Guidelines:\n\n"
        "    Use realistic data and clinical language; do not use placeholders or generic text.\n\n"
        "    Tailor the content to the provided severity level. For example:\n\n"
        "        Severity 1: Describe immediate life-threatening situations (e.g., cardiac arrest).\n\n"
        "        Severity 5: Describe minor, self-limiting complaints (e.g., mild rash).\n\n"
        "    All content should sound like it was written by a real healthcare provider.\n\n"
        "    Avoid mentioning the parameters directly in the report unless naturally included."
    ),

    REPORT_TYPE_TRAFFIC_INCIDENT: (
        "Generate a detailed and realistic traffic incident report based on the following parameters:\n\n"
        "- Date: {date}\n"
        "- Country: {country}\n"
        "- Municipality: {municipality}\n"
        "- Number of vehicles involved: {number_of_vehicles}\n"
        "- Time of day: {time_of_day} (values: night, morning, day, evening)\n"
        "- Weather conditions: {weather_conditions}\n\n"
        "Write the report in a neutral and professional tone, as if authored by a police officer or accident investigator. "
        "The report must include:\n\n"
        "1. A coherent narrative describing what happened, using realistic names for drivers, passengers, and witnesses.\n"
        "2. Fictional but plausible street names and addresses, based on the provided country and municipality.\n"
        "3. A timeline of the events that is consistent with the given time of day and date.\n"
        "4. Weather and road conditions that match the specified weather conditions and impact the scene as appropriate.\n"
        "5. Realistic but fictional vehicle models, license plates, and damage descriptions.\n"
        "6. No placeholders or parameter names — everything must appear as fully generated, real-world text.\n\n"
        "Ensure that all information in the report logically aligns with the provided parameters. "
        "The output should read as a complete and official report written by a human."
    ),

    REPORT_TYPE_BUILDING_INSPECTION: (
        "Generate an official building inspection report based on the following parameters:\n\n"
        "- Country: {country}\n"
        "- Municipality: {municipality}\n"
        "- Inspection Date: {inspection_date} (format: DD.MM.YYYY)\n"
        "- Building Type: {building_type} (e.g., residential, commercial, industrial, public)\n"
        "- Construction Year: {construction_year}\n\n"
        "Guidelines:\n"
        "1. Generate realistic and consistent values for the following:\n"
        "   - **Number of floors**, appropriate for the building type and construction year.\n"
        "   - **Building material**, based on typical materials used in the country and construction era.\n"
        "   - **Inspector name**, use a realistic human name.\n"
        "   - **Weather conditions**, consistent with the country, region, and season based on the inspection date.\n"
        "   - **Noted issues**, relevant to the age, type, and material of the building.\n"
        "   - **Compliance status**, make it realistic based on fictional interpretation of building codes in the given country.\n\n"
        "2. Write the report in a **professional and official tone**, suitable for submission to local or national building authorities.\n\n"
        "3. Include the following sections:\n"
        "   - **1. General Information**: Country, municipality, address (invent one), inspection date, inspector name.\n"
        "   - **2. Building Overview**: Type, construction year, number of floors, primary materials.\n"
        "   - **3. Inspection Context**: Weather conditions on inspection date, purpose of inspection (e.g., routine check, resale, renovation permit).\n"
        "   - **4. Observations and Findings**: Structural, electrical, plumbing, HVAC, fire safety, and accessibility.\n"
        "   - **5. Identified Issues and Recommendations**: List of findings with clear, actionable suggestions.\n"
        "   - **6. Compliance Summary**: Assessment of compliance with local or national building regulations.\n"
        "   - **7. Conclusion**: Overall condition summary, follow-up recommendations if needed, and signature/date.\n\n"
        "4. Do not include placeholders. Use realistic, technically accurate, and country-appropriate content.\n\n"
        "5. Ensure the report reads like an authentic, complete inspection document ready for professional use."
    ),
}

municipalities = [
    "Alajärvi", "Alavieska", "Alavus", "Asikkala", "Askola", "Aura", "Akaa", "Brändö", "Eckerö", "Enonkoski",
    "Enontekiö", "Espoo", "Eura", "Eurajoki", "Evijärvi", "Finström", "Forssa", "Föglö", "Geta", "Haapajärvi",
    "Haapavesi", "Hailuoto", "Halsua", "Hamina", "Hammarland", "Hankasalmi", "Hanko", "Harjavalta", "Hartola",
    "Hattula", "Hausjärvi", "Heinävesi", "Helsinki", "Vantaa", "Hirvensalmi", "Hollola", "Huittinen", "Humppila",
    "Hyrynsalmi", "Hyvinkää", "Hämeenkyrö", "Hämeenlinna", "Heinola", "Ii", "Iisalmi", "Iitti", "Ikaalinen",
    "Ilmajoki", "Ilomantsi", "Inari", "Inkoo", "Isojoki", "Isokyrö", "Imatra", "Janakkala", "Joensuu", "Jokioinen",
    "Jomala", "Joroinen", "Joutsa", "Juuka", "Juupajoki", "Juva", "Jyväskylä", "Jämijärvi", "Jämsä", "Järvenpää",
    "Kaarina", "Kaavi", "Kajaani", "Kalajoki", "Kangasala", "Kangasniemi", "Kankaanpää", "Kannonkoski", "Kannus",
    "Karijoki", "Karkkila", "Karstula", "Karvia", "Kaskinen", "Kauhajoki", "Kauhava", "Kauniainen", "Kaustinen",
    "Keitele", "Kemi", "Keminmaa", "Kempele", "Kerava", "Keuruu", "Kihniö", "Kinnula", "Kirkkonummi", "Kitee",
    "Kittilä", "Kiuruvesi", "Kivijärvi", "Kokemäki", "Kokkola", "Kolari", "Konnevesi", "Kontiolahti", "Korsnäs",
    "Koski Tl", "Kotka", "Kouvola", "Kristiinankaupunki", "Kruunupyy", "Kuhmo", "Kuhmoinen", "Kumlinge", "Kuopio",
    "Kuortane", "Kurikka", "Kustavi", "Kuusamo", "Outokumpu", "Kyyjärvi", "Kärkölä", "Kärsämäki", "Kökar",
    "Kemijärvi", "Kemiönsaari", "Lahti", "Laihia", "Laitila", "Lapinlahti", "Lappajärvi", "Lappeenranta",
    "Lapinjärvi", "Lapua", "Laukaa", "Lemi", "Lemland", "Lempäälä", "Leppävirta", "Lestijärvi", "Lieksa", "Lieto",
    "Liminka", "Liperi", "Loimaa", "Loppi", "Loviisa", "Luhanka", "Lumijoki", "Lumparland", "Luoto", "Luumäki",
    "Lohja", "Parainen", "Maalahti", "Maarianhamina", "Marttila", "Masku", "Merijärvi", "Merikarvia", "Miehikkälä",
    "Mikkeli", "Muhos", "Multia", "Muonio", "Mustasaari", "Muurame", "Mynämäki", "Myrskylä", "Mäntsälä",
    "Mäntyharju", "Mänttä-Vilppula", "Naantali", "Nakkila", "Nivala", "Nokia", "Nousiainen", "Nurmes", "Nurmijärvi",
    "Närpiö", "Orimattila", "Oripää", "Orivesi", "Oulainen", "Oulu", "Padasjoki", "Paimio", "Paltamo", "Parikkala",
    "Parkano", "Pelkosenniemi", "Perho", "Petäjävesi", "Pieksämäki", "Pielavesi", "Pietarsaari", "Pedersören kunta",
    "Pihtipudas", "Pirkkala", "Polvijärvi", "Pomarkku", "Pori", "Pornainen", "Posio", "Pudasjärvi", "Pukkila",
    "Punkalaidun", "Puolanka", "Puumala", "Pyhtää", "Pyhäjoki", "Pyhäjärvi", "Pyhäntä", "Pyhäranta", "Pälkäne",
    "Pöytyä", "Porvoo", "Raahe", "Raisio", "Rantasalmi", "Ranua", "Rauma", "Rautalampi", "Rautavaara", "Rautjärvi",
    "Reisjärvi", "Riihimäki", "Ristijärvi", "Rovaniemi", "Ruokolahti", "Ruovesi", "Rusko", "Rääkkylä", "Raasepori",
    "Saarijärvi", "Salla", "Salo", "Saltvik", "Sauvo", "Savitaipale", "Savonlinna", "Savukoski", "Seinäjoki", "Sievi",
    "Siikainen", "Siikajoki", "Siilinjärvi", "Simo", "Sipoo", "Siuntio", "Sodankylä", "Soini", "Somero", "Sonkajärvi",
    "Sotkamo", "Sottunga", "Sulkava", "Sund", "Suomussalmi", "Suonenjoki", "Sysmä", "Säkylä", "Vaala", "Sastamala",
    "Siikalatva", "Taipalsaari", "Taivalkoski", "Taivassalo", "Tammela", "Tampere", "Tervo", "Tervola", "Teuva",
    "Tohmajärvi", "Toholampi", "Toivakka", "Tornio", "Turku", "Pello", "Tuusniemi", "Tuusula", "Tyrnävä", "Ulvila",
    "Urjala", "Utajärvi", "Utsjoki", "Uurainen", "Uusikaarlepyy", "Uusikaupunki", "Vaasa", "Valkeakoski", "Varkaus",
    "Vehmaa", "Vesanto", "Vesilahti", "Veteli", "Vieremä", "Vihti", "Viitasaari", "Vimpeli", "Virolahti", "Virrat",
    "Vårdö", "Vöyri", "Ylitornio", "Ylivieska", "Ylöjärvi", "Ypäjä", "Ähtäri", "Äänekoski",
]


def random_past_date(days_before_now: int) -> str:
    """
    Returns a random date string in format "D.M.YYYY" from the past,
    between today and 'days_before_now' days ago (inclusive).
    """
    now = datetime.now()
    start_date = now - timedelta(days=days_before_now)
    random_date = start_date + timedelta(days=random.randint(0, days_before_now))
    return random_date.strftime("%d.%m.%Y")


def random_year(start_year: int) -> int:
    """
    Returns a random year between start_year and the current year (inclusive).
    """
    current_year = datetime.now().year
    return random.randint(start_year, current_year)


def get_industry():
    industries = [
        "Manufacturing", "Healthcare", "Finance", "Retail", "Energy",
        "Telecommunications", "Transportation", "Education", "Government",
        "Pharmaceuticals", "Construction", "Utilities", "Insurance", "Technology",
    ]
    return random.choice(industries)


def get_project_name(industry):
    project_names = {
        "Manufacturing": [
            "Factory Automation Overhaul", "ERP Modernization Program",
            "Smart Supply Chain Deployment", "Lean Manufacturing Initiative",
        ],
        "Healthcare": [
            "Electronic Health Record Migration", "Patient Portal Implementation",
            "Medical Device Integration Rollout", "Hospital Expansion Project",
        ],
        "Finance": [
            "Core Banking Platform Upgrade", "AI-Powered Fraud Detection System",
            "Regulatory Compliance Automation", "Wealth Management Suite Deployment",
        ],
        "Retail": [
            "Omnichannel Sales System Launch", "POS System Replacement",
            "Warehouse Digitization Project", "Customer Loyalty Platform Upgrade",
        ],
        "Energy": [
            "Smart Grid Rollout", "Green Hydrogen Plant Construction",
            "Pipeline Monitoring System Deployment", "Carbon Capture Pilot Project",
        ],
        "Telecommunications": [
            "5G Tower Infrastructure Buildout", "Fiber Network Expansion",
            "Billing System Replacement", "Customer Self-Service Portal Upgrade",
        ],
        "Transportation": [
            "Fleet Management Platform Implementation", "Airport Baggage System Upgrade",
            "Autonomous Vehicle Pilot", "Rail Scheduling Optimization",
        ],
        "Education": [
            "Digital Classroom Initiative", "Student Records Modernization",
            "Learning Analytics Platform Deployment", "Campus WiFi Upgrade",
        ],
        "Government": [
            "Public Records Digitization", "Smart City Infrastructure Pilot",
            "Civic Engagement Platform", "Cybersecurity Modernization Program",
        ],
        "Pharmaceuticals": [
            "Clinical Trial Data Platform", "Regulatory Submissions Portal",
            "Drug Manufacturing Quality System", "Laboratory Equipment Upgrade",
        ],
        "Construction": [
            "High-Rise Residential Project", "Urban Transit Hub Construction",
            "Modular Housing Development", "New Logistics Center Build",
        ],
        "Utilities": [
            "Smart Meter Installation", "Power Grid Resilience Upgrade",
            "Water Treatment Plant Renovation", "Outage Management System Implementation",
        ],
        "Insurance": [
            "Claims Automation Engine", "Policy Admin System Modernization",
            "Risk Modeling Platform Rollout", "Customer Portal Migration",
        ],
        "Technology": [
            "Cloud Migration Project", "AI Recommendation Engine",
            "Enterprise SaaS Platform Development", "DevOps Toolchain Rollout",
        ],
    }
    return random.choice(project_names.get(industry, ["Generic Strategic Initiative"]))


def get_quarter():
    current_year = datetime.now().year
    year = random.choice(range(current_year - 2, current_year + 1))
    quarter = random.choice(["Q1", "Q2", "Q3", "Q4"])
    return f"{quarter} {year}"


def get_project_stage():
    stages = [
        "Initiation", "Requirements Gathering", "Design Phase", "Procurement",
        "Implementation", "System Integration", "Testing", "Deployment",
        "Go-Live", "Post-Go-Live Support", "Monitoring & Evaluation", "Project Closure",
    ]
    return random.choice(stages)


def get_primary_blocker(industry):
    common_blockers = {
        "default": [
            "Budget overruns", "Staff turnover", "Regulatory delays",
            "Stakeholder misalignment", "Scope creep", "Vendor delays",
            "Integration issues", "Lack of executive support", "Insufficient training",
            "Late deliverables", "Data quality issues", "Procurement holdup",
        ],
        "Construction": [
            "Weather-related delays", "Permit approval delays", "Equipment shortages",
            "Labor union disputes", "Site contamination discovered",
        ],
        "Healthcare": [
            "EHR integration issues", "HIPAA compliance challenges",
            "Clinical staff resistance", "Device certification delays",
        ],
        "Finance": [
            "Compliance scope changes", "Data privacy concerns",
            "Delayed third-party audits", "Legacy system constraints",
        ],
        "Energy": [
            "Environmental review holdups", "Specialized labor shortage",
            "Permit delays", "Supply chain instability", "On-site safety incidents",
        ],
    }
    blockers = common_blockers.get(industry, []) + common_blockers["default"]
    return random.choice(blockers)


def get_visit_type():
    visit_types = [
        "Child welfare check",
        "Elderly care follow-up",
        "Domestic violence risk assessment",
        "Post-hospital discharge visit",
        "Substance abuse support visit",
        "Disability support assessment",
        "Foster family evaluation",
        "Homeless outreach visit",
        "Parental capacity evaluation",
        "Routine family wellbeing visit",
        "Mental health monitoring visit",
        "Newborn and infant safety visit",
        "Unaccompanied minor intake assessment",
        "Follow-up on school truancy report",
        "Household financial hardship review",
        "Immigration case monitoring visit",
        "Family reunification progress check",
        "At-risk youth intervention visit",
        "Refugee integration support visit",
        "Domestic relocation follow-up",
        "Emergency housing verification",
        "Post-abuse recovery support visit",
        "Veteran support service check-in",
        "Support plan review meeting",
        "Juvenile probation compliance visit",
        "Social reintegration assessment",
        "Child visitation supervision report",
        "Safety plan monitoring visit",
        "Parenting education follow-up",
        "Youth mentoring program assessment",
    ]
    return random.choice(visit_types)


def get_household_composition():
    compositions = [
        "Single mother with three children",
        "Elderly couple living independently",
        "Young adult living alone",
        "Single father with one child",
        "Grandparents caring for grandchildren",
        "Married couple with four children",
        "Teenager in foster care",
        "Mother and newborn infant",
        "Two adult siblings sharing housing",
        "Single adult with physical disability",
        "Elderly woman with early dementia symptoms",
        "Separated couple with shared custody",
        "Unaccompanied minor in temporary housing",
        "Family of five in subsidized apartment",
        "Adult living with severe mental health condition",
        "Young couple expecting their first child",
        "Disabled adult and live-in caregiver",
        "Woman recovering from domestic abuse",
        "Teenager with school attendance issues",
        "Immigrant family recently relocated",
        "Parent with substance use disorder and children",
        "Elderly man living with adult daughter",
        "Refugee family in temporary accommodation",
        "Teenage mother and infant living with parents",
        "Rehabilitated ex-offender reintegrating into society",
        "Multi-generational household with financial difficulties",
        "Single adult with intellectual disability",
        "Two-parent household with reported neglect case",
        "Transitional housing residents post-rehabilitation",
        "Family with history of chronic domestic violence",
        "Cohabiting couple with mental health challenges",
        "Single caregiver supporting elderly parent with dementia",
        "Child living with non-custodial relative",
        "Youth aging out of foster system",
        "Blended family with recent custody changes",
    ]
    return random.choice(compositions)


def get_case_severity():
    severities = ["Low", "Moderate", "High", "Urgent", "Critical"]
    weights = [0.35, 0.35, 0.15, 0.10, 0.05]
    return random.choices(severities, weights=weights, k=1)[0]


def create_doctor_visit_request():
    severity_levels = [1, 2, 3, 4, 5]
    patient_gender = ["male", "female"]
    patient_age = list(range(1, 106))
    request_json = {}
    request_json["location"] = random.choice(municipalities)
    request_json["date"] = random_past_date(730)
    request_json["patient_age"] = random.choice(patient_age)
    request_json["patient_gender"] = random.choice(patient_gender)
    # Key is "severity" to match the {severity} placeholder in the prompt template.
    request_json["severity"] = random.choice(severity_levels)
    return request_json


def create_traffic_incident_request():
    number_of_vehicles = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                          3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 5, 6, 7, 8, 9, 10, 11]
    time_of_day = ["night", "morning", "day", "evening"]
    weather_conditions = [
        "Clear and sunny", "Overcast", "Light rain", "Heavy rain", "Foggy",
        "Snowy", "Icy roads", "Windy with gusts", "Thunderstorm",
        "Dry but cold", "Wet and slippery", "Mixed snow and rain",
    ]
    request_json = {}
    request_json["municipality"] = random.choice(municipalities)
    request_json["country"] = "Finland"
    request_json["date"] = random_past_date(1000)
    request_json["number_of_vehicles"] = random.choice(number_of_vehicles)
    request_json["time_of_day"] = random.choice(time_of_day)
    request_json["weather_conditions"] = random.choice(weather_conditions)
    return request_json


def create_building_inspection_request():
    building_type = ["residential", "commercial", "industrial", "public"]
    request_json = {}
    request_json["municipality"] = random.choice(municipalities)
    request_json["country"] = "Finland"
    request_json["inspection_date"] = random_past_date(365)
    request_json["construction_year"] = random_year(1970)
    request_json["building_type"] = random.choice(building_type)
    return request_json


def create_project_update_request():
    industry = get_industry()
    request_json = {}
    request_json["industry"] = industry
    request_json["quarter"] = get_quarter()
    request_json["primary_blocker"] = get_primary_blocker(industry)
    request_json["project_name"] = get_project_name(industry)
    request_json["project_stage"] = get_project_stage()
    return request_json


def create_social_services_visit_request():
    request_json = {}
    request_json["municipality"] = random.choice(municipalities)
    request_json["country"] = "Finland"
    request_json["date"] = random_past_date(365)
    request_json["case_severity"] = get_case_severity()
    request_json["household_composition"] = get_household_composition()
    request_json["visit_type"] = get_visit_type()
    return request_json


def fill_prompt(report_type, request_json):
    """Return the prompt template for report_type with all placeholders filled."""
    return PROMPT_TEMPLATES[report_type].format_map(request_json)


def call_ollama(prompt, ollama_model_tag):
    """
    POST the filled prompt to the local Ollama API.
    Returns the generated text string, or None on failure.
    """
    payload = {"model": ollama_model_tag, "prompt": prompt, "stream": False}
    try:
        response = requests.post(
            OLLAMA_API_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=300,
        )
        if response.status_code != 200:
            print(f"ERROR: Ollama returned HTTP {response.status_code}: {response.text}")
            return None
        return response.json().get("response", "")
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: Failed to reach Ollama at {OLLAMA_API_URL}: {exc}")
        return None


def _model_slug(model_tag):
    """Convert an Ollama model tag to a filesystem-safe string, e.g. 'qwen2.5:3b' -> 'qwen2.5_3b'."""
    return model_tag.replace(":", "_").replace("/", "_")


def save_report(text, report_type, model_tag, output_dir):
    """
    Save the generated report text as a .md file.
    Filename: {report_type}_{model_slug}_{YYYYMMDD_HHMMSS}.md
    Returns the full path of the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{_model_slug(model_tag)}_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    return filepath


def list_llm_models():
    """Print all models available on the local Ollama server."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=10)
        if response.status_code != 200:
            print(f"ERROR: Ollama returned HTTP {response.status_code}: {response.text}")
            sys.exit(1)
        models = response.json().get("models", [])
        if not models:
            print("No models found on local Ollama server.")
            return
        print(f"Available models ({len(models)}):")
        for model in models:
            name = model.get("name", "")
            size_bytes = model.get("size", 0)
            size_gb = size_bytes / (1024 ** 3)
            print(f"  {name:<35} {size_gb:.1f} GB")
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: Failed to reach Ollama at {OLLAMA_TAGS_URL}: {exc}")
        sys.exit(1)


def error(msg):
    print("ERROR: " + msg)
    sys.exit(1)


def generate_reports(report_type, llm_models, count, sleep, output_dir):
    print(f"Generating {count} report(s) of type '{report_type}' using model(s) {llm_models}...")

    for i in range(1, count + 1):
        if report_type == REPORT_TYPE_DOCTOR_VISIT:
            request_json = create_doctor_visit_request()
        elif report_type == REPORT_TYPE_TRAFFIC_INCIDENT:
            request_json = create_traffic_incident_request()
        elif report_type == REPORT_TYPE_BUILDING_INSPECTION:
            request_json = create_building_inspection_request()
        elif report_type == REPORT_TYPE_PROJECT_UPDATE:
            request_json = create_project_update_request()
        elif report_type == REPORT_TYPE_SOCIAL_SERVICES_VISIT:
            request_json = create_social_services_visit_request()
        else:
            error(f"Unknown report type: {report_type}")

        prompt = fill_prompt(report_type, request_json)
        minified = json.dumps(request_json, separators=(",", ":"))

        for model_tag in llm_models:
            print(f"[{i}/{count}] {report_type} - {model_tag} - {minified}")
            text = call_ollama(prompt, model_tag)
            if text is None:
                print(f"  SKIPPED (Ollama error)")
            else:
                path = save_report(text, report_type, model_tag, output_dir)
                print(f"  Saved: {path}")

            if sleep > 0 and not (i == count and model_tag == llm_models[-1]):
                print(f"  Sleeping {sleep} seconds...")
                time.sleep(sleep)


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to generate synthetic reports via a local Ollama server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--list-llm-models",
        action="store_true",
        default=False,
        help="List all models available on the local Ollama server and exit.",
    )

    parser.add_argument(
        "--report-type",
        type=str,
        choices=AVAILABLE_REPORT_TYPES,
        help="Type of report to generate.",
    )

    parser.add_argument(
        "--llm-model",
        type=str,
        nargs="+",
        help="Ollama model tag(s) to use, e.g. 'llama3.2:3b' or 'qwen2.5:3b'. "
             "Multiple tags can be provided to generate reports with each.",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of reports to generate.",
    )

    parser.add_argument(
        "--sleep",
        type=int,
        default=0,
        help="Seconds to sleep between calls to Ollama.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./reports/",
        help="Directory where generated .md report files are saved.",
    )

    args = parser.parse_args()

    if args.list_llm_models:
        list_llm_models()
        sys.exit(0)

    if not args.report_type:
        parser.error("--report-type is required when not using --list-llm-models.")
    if not args.llm_model:
        parser.error("--llm-model is required when not using --list-llm-models.")

    generate_reports(args.report_type, args.llm_model, args.count, args.sleep, args.output_dir)


if __name__ == "__main__":
    main()
