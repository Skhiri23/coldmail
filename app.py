"""
Application de candidature spontanée
-------------------------------------
Formulaire simple : tu entres le nom de la société + l'email du destinataire,
tu choisis la langue de la lettre et la langue du CV, l'appli génère une
lettre de motivation personnalisée et envoie un mail avec ton CV en pièce
jointe.

Lancement :
    python app.py
Puis ouvre http://127.0.0.1:5000 dans ton navigateur.

Configuration : copie .env.example en .env et remplis tes identifiants.
"""

import os
import smtplib
import mimetypes
from email.message import EmailMessage

from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

# ---------------------------------------------------------------------------
# Configuration (lue depuis .env)
# ---------------------------------------------------------------------------
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

SENDER_NAME = os.environ.get("SENDER_NAME", "Mohamed Aziz Skhiri")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") or os.environ.get("SMTP_USER") or "azizskhiri107@gmail.com"
SENDER_PHONE = os.environ.get("SENDER_PHONE", "+216 52 237 532")
LINKEDIN_URL = os.environ.get("LINKEDIN_URL", "linkedin.com/in/mohamed-aziz-skhiri-498627254")
PORTFOLIO_URL = os.environ.get("PORTFOLIO_URL", "skhiri23.github.io")

POSTE_FR = os.environ.get("POSTE_FR", "Data Scientist / IA & ML Engineer")
POSTE_EN = os.environ.get("POSTE_EN", "Data Scientist / AI & ML Engineer")

CV_DIR = os.path.join(os.path.dirname(__file__), "cv")
CV_PATH_FR = os.environ.get("CV_PATH_FR", os.path.join(CV_DIR, "CV_FR.pdf"))
CV_PATH_EN = os.environ.get("CV_PATH_EN", os.path.join(CV_DIR, "CV_EN.pdf"))

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ---------------------------------------------------------------------------
# Templates de lettre de motivation
# ---------------------------------------------------------------------------

SUBJECT_FR = "Candidature spontanée – {poste}"
SUBJECT_EN = "Spontaneous application – {poste}"

TEMPLATE_FR = """Madame, Monsieur,

Je suis récemment diplômé d'un Master en Data Science et je suis actuellement à la recherche d'une opportunité en tant que {poste}.

Mon profil est à la croisée de la Data Science, du Machine Learning et du développement logiciel. Je travaille principalement avec Python, Pandas, NumPy, Scikit-learn, XGBoost, TensorFlow/Keras, SQL et PostgreSQL, et je sais également transformer un modèle en une solution exploitable grâce à Flask/FastAPI, React, Docker et AWS.

Mon expérience la plus significative est mon projet de fin d'études réalisé chez Nouvelair Tunisie, où j'ai développé FuelTrack, une plateforme intelligente de suivi et de prédiction de la consommation de carburant et des émissions CO2. J'y ai travaillé sur toute la chaîne : préparation des données, feature engineering, modèles XGBoost/LSTM, évaluation, SHAP, API Flask, PostgreSQL, React et dashboards Power BI. J'ai également intégré un module RAG avec LLaMA pour permettre une interaction avec les données de vols en langage naturel.

Cette expérience m'a surtout appris à ne pas m'arrêter au modèle : partir d'un problème métier, travailler la donnée, construire le modèle puis l'intégrer dans une véritable application. C'est précisément ce type de projets que je souhaite continuer à développer chez {company}.

Je serais donc ravi d'échanger avec vous au sujet de vos besoins actuels ou futurs en Data, Machine Learning et Intelligence Artificielle, même si aucun poste correspondant à mon profil n'est actuellement publié.

Merci pour votre attention, et au plaisir d'échanger avec vous.

{sender_name}
{sender_phone}
{sender_email}
LinkedIn : {linkedin}
Portfolio : {portfolio}
"""

TEMPLATE_EN = """Dear Hiring Manager,

I recently graduated with a Master's degree in Data Science and I am currently looking for an opportunity as a {poste}.

My profile sits at the intersection of Data Science, Machine Learning and software development. I mainly work with Python, Pandas, NumPy, Scikit-learn, XGBoost, TensorFlow/Keras, SQL and PostgreSQL, and I'm also able to turn a model into a usable product using Flask/FastAPI, React, Docker and AWS.

My most significant experience is my capstone project at Nouvelair Tunisie, where I built FuelTrack, an intelligent platform to track and predict aircraft fuel consumption and CO2 emissions. I worked across the full chain: data preparation, feature engineering, XGBoost/LSTM models, evaluation, SHAP, a Flask API, PostgreSQL, React and Power BI dashboards. I also integrated a RAG module with LLaMA to enable natural-language interaction with flight data.

This experience mainly taught me not to stop at the model: start from a business problem, work the data, build the model, then integrate it into a real application. This is exactly the kind of project I want to keep working on at {company}.

I would therefore be delighted to discuss your current or future needs in Data, Machine Learning and Artificial Intelligence, even if no position matching my profile is currently open.

Thank you for your time, and I look forward to hearing from you.

{sender_name}
{sender_phone}
{sender_email}
LinkedIn: {linkedin}
Portfolio: {portfolio}
"""


def generate_cover_letter(company: str, lang: str = "fr") -> tuple[str, str]:
    """Retourne (sujet, corps du mail) dans la langue demandée ('fr' ou 'en').
    Utilise Claude si une clé API est configurée pour une lettre plus
    personnalisée, sinon retombe sur le template ci-dessus."""
    company = company.strip()
    lang = "en" if lang == "en" else "fr"

    if ANTHROPIC_API_KEY:
        try:
            return _generate_with_claude(company, lang)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] génération IA échouée ({exc}), utilisation du template.")

    if lang == "en":
        subject = SUBJECT_EN.format(poste=POSTE_EN, company=company)
        body = TEMPLATE_EN.format(
            poste=POSTE_EN,
            company=company,
            sender_name=SENDER_NAME,
            sender_phone=SENDER_PHONE,
            sender_email=SENDER_EMAIL,
            linkedin=LINKEDIN_URL,
            portfolio=PORTFOLIO_URL,
        )
    else:
        subject = SUBJECT_FR.format(poste=POSTE_FR, company=company)
        body = TEMPLATE_FR.format(
            poste=POSTE_FR,
            company=company,
            sender_name=SENDER_NAME,
            sender_phone=SENDER_PHONE,
            sender_email=SENDER_EMAIL,
            linkedin=LINKEDIN_URL,
            portfolio=PORTFOLIO_URL,
        )
    return subject, body


def _generate_with_claude(company: str, lang: str) -> tuple[str, str]:
    """Génération optionnelle via l'API Anthropic pour varier/affiner le texte."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    profile = """
Mohamed Aziz Skhiri — Data Scientist / AI-ML Engineer junior.
Professional Master's in Data Science (FSM, University of Monastir, 2024-2026).
Stack: Python, SQL, Scikit-learn, XGBoost, TensorFlow/Keras, Flask, React, Docker, AWS.
Capstone internship at Nouvelair Tunisie (IT Technology & Projects dept, Feb-Jun 2026, with
ATDS): built FuelTrack, an intelligent platform to track/analyze/predict aircraft fuel
consumption and CO2 emissions, replacing a manual LIDO Flight / PDC FlightOps / Excel OFP
workflow. Built predictive models (XGBoost, Gradient Boosting, Random Forest, LSTM) with
registration-based bias correction; built a RAG conversational module (Groq LLaMA 3.3-70B,
Gemini 2.5 Flash fallback) over SQL-aggregated flight data; built a full-stack Flask/
PostgreSQL/React app with JWT auth and role-based access (admin, analyst, pilot, viewer);
followed hybrid SCRUM + CRISP-DM over 6 sprints under academic supervisor Ms. Leila Ghorbel
and industry supervisors Mr. Ramzi Fazzi and Mr. Ghayth Ajra.
Other projects: NLP email assistant, football data pipeline, HRMS, AI school attendance
system, global health Streamlit dashboard.
Key strengths to highlight: end-to-end delivery (data -> model -> API -> dashboard), rare
junior combo of data science + full-stack dev, hands-on GenAI/RAG experience, agile
methodology with real business stakeholders, fast learner, autonomous, business-first mindset.
""".strip()

    lang_name = "English" if lang == "en" else "French"
    poste = POSTE_EN if lang == "en" else POSTE_FR

    prompt = f"""Write a spontaneous job application email in {lang_name}, professional and
polished (220-280 words), addressed to the company "{company}", for a "{poste}" position.
Use this candidate profile (do not invent anything beyond it):
{profile}

Follow this structure closely (this is a fixed template the candidate likes, vary the wording
but keep the structure and balance):
1. Opening: recently graduated with a Master's in Data Science, currently looking for an
   opportunity as {poste}.
2. A paragraph on SKILLS first: the profile sits at the intersection of Data Science, Machine
   Learning and software development — Python, Pandas, NumPy, Scikit-learn, XGBoost,
   TensorFlow/Keras, SQL, PostgreSQL, plus turning a model into a real product with
   Flask/FastAPI, React, Docker, AWS.
3. A brief paragraph on the Nouvelair Tunisie / FuelTrack capstone internship as proof: what
   it is (fuel consumption / CO2 prediction platform), and the range of things worked on
   (data prep, feature engineering, XGBoost/LSTM, evaluation/SHAP, Flask API, PostgreSQL,
   React, Power BI dashboards, a RAG module with LLaMA for natural-language queries on flight
   data) — kept concise, not a bullet list.
4. A short paragraph on what that experience taught him: not stopping at the model, going
   from business problem to data to model to a real integrated application — and wanting to
   keep working on {company}'s kind of projects.
5. A closing paragraph offering to discuss the company's current or future Data/ML/AI needs,
   even if no matching position is currently open.
6. Polite closing and this exact signature:
{SENDER_NAME}
{SENDER_PHONE}
{SENDER_EMAIL}
LinkedIn: {LINKEDIN_URL}
Portfolio: {PORTFOLIO_URL}

Additional constraints:
- Mention the company name naturally, at most twice.
- Do not include a subject line in the body.
- Reply ONLY with the email body, nothing else.
"""

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    body = "".join(block.text for block in message.content if block.type == "text").strip()
    subject = (SUBJECT_EN if lang == "en" else SUBJECT_FR).format(poste=poste, company=company)
    return subject, body


# ---------------------------------------------------------------------------
# Envoi de l'e-mail
# ---------------------------------------------------------------------------

def _resolve_cv_path(cv_lang: str) -> str:
    wanted = CV_PATH_EN if cv_lang == "en" else CV_PATH_FR
    other = CV_PATH_FR if cv_lang == "en" else CV_PATH_EN
    if os.path.exists(wanted):
        return wanted
    if os.path.exists(other):
        return other
    return wanted  # n'existe pas, l'appelant lèvera une erreur claire


def send_application_email(to_email: str, company: str, letter_lang: str, cv_lang: str) -> None:
    subject, body = generate_cover_letter(company, letter_lang)
    cv_path = _resolve_cv_path(cv_lang)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg.set_content(body)

    if os.path.exists(cv_path):
        ctype, _ = mimetypes.guess_type(cv_path)
        maintype, subtype = (ctype or "application/pdf").split("/", 1)
        with open(cv_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(cv_path),
            )
    else:
        raise FileNotFoundError(
            f"Aucun CV trouvé (cherché : {CV_PATH_FR} et {CV_PATH_EN}) — "
            "place au moins un des deux fichiers dans le dossier cv/."
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    configured = bool(SMTP_USER and SMTP_PASSWORD)
    return render_template(
        "index.html",
        configured=configured,
        cv_fr_exists=os.path.exists(CV_PATH_FR),
        cv_en_exists=os.path.exists(CV_PATH_EN),
    )


@app.route("/send", methods=["POST"])
def send():
    company = request.form.get("company", "").strip()
    to_email = request.form.get("email", "").strip()
    letter_lang = request.form.get("letter_lang", "fr")
    cv_lang = request.form.get("cv_lang", "fr")

    if not company or not to_email:
        flash("Merci de remplir le nom de la société et l'email.", "error")
        return redirect(url_for("index"))

    if not (SMTP_USER and SMTP_PASSWORD):
        flash("Configuration SMTP manquante : remplis ton fichier .env (voir .env.example).", "error")
        return redirect(url_for("index"))

    try:
        send_application_email(to_email, company, letter_lang, cv_lang)
        flash(f"Candidature envoyée avec succès à {company} ({to_email}) ✅", "success")
    except Exception as exc:  # noqa: BLE001
        flash(f"Échec de l'envoi : {exc}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
