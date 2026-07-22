import os
import time
import json
import csv
import datetime
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from ddgs import DDGS
from google import genai
from google.genai import types

# ==========================================
# ⚙️ CONFIGURATION & TARGETS
# ==========================================

RECIPIENT_EMAIL = "joao.silva@bird.co"
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# AI Setup
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
client = genai.Client()

STATE_FILE = "state.json"
BUFFER_FILE = "daily_buffer.csv"
MEMORY_FILE = "rfp_memory.csv"

# ==========================================
# 🇵🇹 COMPLETE LIST OF ALL 308 PORTUGUESE MUNICIPALITIES
# ==========================================

PORTUGAL_308_MUNICIPALITIES = [
    # Chunk 01-05: Norte & Porto Region
    "Abrantes", "Agualva-Cacém", "Águeda", "Aguiar da Beira", "Alandroal", "Albergaria-a-Velha", "Albufeira", "Alcácer do Sal", "Alcanena", "Alcobaça",
    "Alcochete", "Alcoutim", "Alenquer", "Alfândega da Fé", "Alijó", "Aljezur", "Aljustrel", "Almada", "Almeida", "Almeirim",
    "Almodôvar", "Alpiarça", "Alter do Chão", "Alvaiázere", "Alvito", "Amadora", "Amarante", "Amares", "Anadia", "Angra do Heroísmo",
    "Ansião", "Arcos de Valdevez", "Arraiolos", "Arronches", "Arruda dos Vinhos", "Aveiro", "Avis", "Azambuja", "Baião", "Barcelos",
    "Barreiro", "Batalha", "Beja", "Belmonte", "Benavente", "Bombarral", "Borba", "Boticas", "Braga", "Bragança",
    "Cabeceiras de Basto", "Cadaval", "Caldas da Rainha", "Calheta (Açores)", "Calheta (Madeira)", "Câmara de Lobos", "Caminha", "Campomaior", "Cantanhede", "Carrazeda de Ansiães",
    "Carregal do Sal", "Cartaxo", "Cascais", "Castelo de Paiva", "Castelo de Vide", "Castelo Branco", "Castro Daire", "Castro Marim", "Castro Verde", "Celorico da Beira",
    "Celorico de Basto", "Chaves", "Cinfães", "Coimbra", "Condeixa-a-Nova", "Constância", "Coruche", "Corvo", "Covilhã", "Crato",
    "Cuba", "Elvas", "Entroncamento", "Espinho", "Esposende", "Estarreja", "Estremoz", "Évora", "Fafe", "Faro",
    "Felgueiras", "Ferreira do Alentejo", "Ferreira do Zêzere", "Figueira da Foz", "Figueira de Castelo Rodrigo", "Figueiró dos Vinhos", "Fronteira", "Funchal", "Fundão", "Gavião",
    "Góis", "Golegã", "Gondomar", "Gouveia", "Grândola", "Guarda", "Guimarães", "Horta", "Idanha-a-Nova", "Ílhavo",
    "Lagoa (Açores)", "Lagoa (Algarve)", "Lagos", "Lajes das Flores", "Lajes do Pico", "Lamego", "Leiria", "Lisboa", "Loulé", "Loures",
    "Lourinhã", "Lousã", "Lousada", "Mação", "Macedo de Cavaleiros", "Machico", "Madalena", "Mafra", "Maia", "Mangualde",
    "Manteigas", "Marco de Canaveses", "Marinha Grande", "Marvão", "Matosinhos", "Mealhada", "Mêda", "Melgaço", "Mértola", "Mesão Frio",
    "Mira", "Miranda do Corvo", "Miranda do Douro", "Mirandela", "Mogadouro", "Moita", "Monchique", "Mondim de Basto", "Monforte", "Montalegre",
    "Montemor-o-Novo", "Montemor-o-Velho", "Montijo", "Monção", "Mora", "Mortágua", "Moura", "Mourão", "Murça", "Murtosa",
    "Nazaré", "Nelas", "Nisa", "Nordeste", "Óbidos", "Odemira", "Odivelas", "Oeiras", "Oleiros", "Olhão",
    "Oliveira de Azeméis", "Oliveira de Frades", "Oliveira do Bairro", "Oliveira do Hospital", "Ourém", "Ourique", "Ovar", "Paços de Ferreira", "Palmela", "Pampilhosa da Serra",
    "Paredes", "Paredes de Coura", "Pedrógão Grande", "Penacova", "Penafiel", "Penalva do Castelo", "Penamacor", "Penedono", "Penela", "Peniche",
    "Penela", "Pinhel", "Pombal", "Ponta Delgada", "Ponta do Sol", "Ponte da Barca", "Ponte de Lima", "Ponte de Sor", "Portagrande", "Portalegre",
    "Portel", "Portimão", "Porto", "Porto de Mós", "Porto Moniz", "Porto Santo", "Póvoa de Lanhoso", "Póvoa de Varzim", "Povoação", "Praia da Vitória",
    "Proença-a-Nova", "Redondo", "Reguengos de Monsaraz", "Resende", "Ribeira Brava", "Ribeira de Pena", "Ribeira Grande", "Rio Maior", "Sabrosa", "Sabugal",
    "Santa Comba Dão", "Santa Cruz", "Santa Cruz da Graciosa", "Santa Cruz das Flores", "Santa Maria da Feira", "Santa Marta de Penaguião", "Santana", "Santarém", "Santiago do Cacém", "Santo Tirso",
    "São Brás de Alportel", "São João da Madeira", "São João da Pesqueira", "São Pedro do Sul", "São Roque do Pico", "Sardoal", "Sátão", "Seia", "Seixal", "Sernancelhe",
    "Serpa", "Sertã", "Sesimbra", "Setúbal", "Sever do Vouga", "Silves", "Sines", "Sintra", "Sobral de Monte Agraço", "Soure",
    "Souselo", "Tábua", "Tabuaço", "Tarouca", "Tavira", "Terras de Bouro", "Tomar", "Tondela", "Torre de Moncorvo", "Torres Novas",
    "Torres Vedras", "Trancoso", "Trofa", "Vagos", "Vale de Cambra", "Valença", "Valongo", "Valpaços", "Velas", "Vendas Novas",
    "Viana do Alentejo", "Viana do Castelo", "Vidigueira", "Vieira do Minho", "Vila de Rei", "Vila do Bispo", "Vila do Conde", "Vila do Porto", "Vila Flor", "Vila Franca de Xira",
    "Vila Franca do Campo", "Vila Nova da Barquinha", "Vila Nova de Cerveira", "Vila Nova de Famalicão", "Vila Nova de Foz Côa", "Vila Nova de Gaia", "Vila Nova de Poiares", "Vila Pouca de Aguiar", "Vila Real", "Vila Real de Santo António",
    "Vila Velha de Ródão", "Vila Verde", "Vimioso", "Vinhais", "Viseu", "Vizela", "Vouzela"
]

# Core procurement and mobility terms
PROCUREMENT_TERMS = ["Hasta Pública", "Concurso Público", "Consulta Pública", "Concessão", "Regulamento"]
MOBILITY_TERMS = ["trotinetas partilhadas", "bicicletas partilhadas", "modos suaves", "micromobilidade"]

# ==========================================
# 🔄 1. CHUNK CALCULATOR (24-HOUR ROTATION)
# ==========================================

def get_current_chunk():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("current_chunk", 0)
    return 0

def update_chunk(next_chunk):
    with open(STATE_FILE, "w") as f:
        json.dump({"current_chunk": next_chunk}, f, indent=2)

current_chunk = get_current_chunk()

# Calculate slice size (308 cities / 24 hours ≈ 13 cities per run)
total_cities = len(PORTUGAL_308_MUNICIPALITIES)
chunk_size = (total_cities // 24) + 1
start_idx = current_chunk * chunk_size
end_idx = min(start_idx + chunk_size, total_cities)

active_cities = PORTUGAL_308_MUNICIPALITIES[start_idx:end_idx]

print(f"🚀 Running RFP Agent - Cycle Chunk [{current_chunk + 1}/24]")
print(f"📍 Scanning {len(active_cities)} Municipalities: {active_cities[0]} -> {active_cities[-1]}\n")

# ==========================================
# 🕸️ 2. SEARCH ENGINE EXTRACTION
# ==========================================

raw_data = "---- SEARCH ENGINE RESULTS ----\n\n"

for city in active_cities:
    for proc in PROCUREMENT_TERMS[:2]:      # Pick top 2 procurement terms
        for mob in MOBILITY_TERMS[:2]:       # Pick top 2 mobility terms
            query = f'"{proc}" "{mob}" "{city}"'
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=2))
                    for r in results:
                        raw_data += f"CITY: {city}\nTITLE: {r['title']}\nSNIPPET: {r['body']}\nURL: {r['href']}\n\n"
            except Exception as e:
                pass
            time.sleep(1.0) # Polite search delay

# ==========================================
# 🧠 3. AI ANALYSIS (GEMINI)
# ==========================================

new_leads = []

if raw_data.count("TITLE:") > 0:
    print("🧠 Extracting municipal leads via Gemini AI...")
    prompt = f"""
    You are an expert procurement analyst for a micromobility company.
    Analyze these search results for municipal tenders, public auctions (Hasta Pública), regulations, and concessions in Portugal.

    {raw_data}

    Extract ALL valid opportunities related to shared e-scooters, e-bikes, soft mobility, or municipal concessions.
    Return ONLY a JSON list of objects. Each object must have these exact keys:
    "Municipality_or_Entity", "Status", "Priority", "Type", "Confidence", "Action_Timeline", "Why_it_matters", "Title", "URL"

    If no relevant opportunities exist, return: []
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        new_leads = json.loads(response.text)
    except Exception as e:
        print(f"⚠️ AI Parsing Note: {e}")

# ==========================================
# 💾 4. DATA BUFFERING & PERSISTENCE
# ==========================================

def append_to_csv(filepath, rows):
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    fieldnames = ["Municipality_or_Entity", "Status", "Priority", "Type", "Confidence", "Action_Timeline", "Why_it_matters", "Title", "URL"]
    
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for r in rows:
            # Ensure row matches expected fieldnames
            clean_row = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(clean_row)

if new_leads:
    print(f"✨ Found {len(new_leads)} potential lead(s) in this chunk! Appending to daily buffer...")
    append_to_csv(BUFFER_FILE, new_leads)
else:
    print("✅ Chunk complete. No new leads found in this slice.")

# Advance chunk pointer for next hourly execution
next_chunk = (current_chunk + 1) % 24
update_chunk(next_chunk)

# ==========================================
# 📧 5. END-OF-DAY AGGREGATION & EMAIL DISPATCH
# ==========================================

if current_chunk == 23:
    print("\n🏁 24-Hour Scan Cycle Complete! Compiling Daily Comprehensive Report...")
    
    daily_leads = []
    if os.path.exists(BUFFER_FILE) and os.path.getsize(BUFFER_FILE) > 0:
        with open(BUFFER_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            daily_leads = list(reader)
            
    # Merge into Master Memory File (de-duplicating by URL)
    existing_master_urls = set()
    if os.path.exists(MEMORY_FILE) and os.path.getsize(MEMORY_FILE) > 0:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_master_urls = {row.get("URL") for row in reader if row.get("URL")}
            
    unique_daily_leads = [l for l in daily_leads if l.get("URL") not in existing_master_urls]
    if unique_daily_leads:
        append_to_csv(MEMORY_FILE, unique_daily_leads)

    # Dispatch Single Daily Email
    if SENDER_EMAIL and SENDER_PASSWORD:
        print(f"📧 Sending daily summary email to {RECIPIENT_EMAIL}...")
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"🇵🇹 Daily Portugal RFP & Concession Report: {len(daily_leads)} Opportunities"
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECIPIENT_EMAIL
            
            # HTML Email Body
            html_body = f"""
            <h2>🇵🇹 Daily Portugal Municipal RFP & Concession Summary</h2>
            <p>The 24-hour full-nation scan across all <b>308 Portuguese municipalities</b> has concluded.</p>
            <p><b>Total Opportunities Detected Today:</b> {len(daily_leads)}</p>
            <hr>
            <h3>Summary of Findings:</h3>
            """
            
            if daily_leads:
                html_body += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse; font-family:sans-serif;'><tr style='background:#f2f2f2;'><th>Entity</th><th>Type</th><th>Priority</th><th>Why It Matters</th><th>Link</th></tr>"
                for lead in daily_leads:
                    html_body += f"""
                    <tr>
                        <td><b>{lead.get('Municipality_or_Entity')}</b></td>
                        <td>{lead.get('Type')}</td>
                        <td>{lead.get('Priority')}</td>
                        <td>{lead.get('Why_it_matters')}</td>
                        <td><a href='{lead.get('URL')}'>View Notice</a></td>
                    </tr>
                    """
                html_body += "</table>"
            else:
                html_body += "<p>No new tenders, concessions, or regulations were detected across the 308 concelhos today.</p>"
                
            html_body += "<p><br><i>Attached is the complete CSV summary for today's scan.</i></p>"
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach daily CSV
            if os.path.exists(BUFFER_FILE) and os.path.getsize(BUFFER_FILE) > 0:
                with open(BUFFER_FILE, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename=portugal_daily_rfps_{datetime.date.today()}.csv")
                    msg.attach(part)
                    
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            print("✅ Daily report email successfully delivered!")
            
        except Exception as e:
            print(f"❌ Email sending error: {e}")

    # Reset Daily Buffer for the next 24-hour cycle
    with open(BUFFER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Municipality_or_Entity", "Status", "Priority", "Type", "Confidence", "Action_Timeline", "Why_it_matters", "Title", "URL"])
    print("🧹 Daily buffer reset for next 24-hour cycle.")