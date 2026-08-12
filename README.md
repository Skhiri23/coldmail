# Candidature spontanée — envoi automatique

Petite application Flask : tu entres le **nom de la société** et l'**email du
recruteur**, tu choisis la **langue de la lettre** (FR/EN) et la **langue du
CV joint** (FR/EN), elle génère une lettre de motivation personnalisée et
envoie le mail avec ton **CV en pièce jointe**.

⚠️ Cette appli envoie de vrais e-mails depuis ton adresse. Elle doit tourner
**sur ta machine**, avec tes propres identifiants — pas dans un environnement
partagé.

## 1. Installation

```bash
cd coldmail
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuration

```bash
cp .env.example .env
```

Puis ouvre `.env` et remplis :

- `SMTP_USER` / `SMTP_PASSWORD` : ton adresse email et ton mot de passe.
  - **Gmail** : il faut activer la validation en 2 étapes puis générer un
    "mot de passe d'application" ici → https://myaccount.google.com/apppasswords
    (ton mot de passe Gmail normal ne fonctionnera pas).
  - **Outlook/Office365** : `SMTP_HOST=smtp.office365.com`, `SMTP_PORT=587`.
  - **Autre fournisseur** : demande les paramètres SMTP à ton hébergeur mail.
- `SENDER_NAME`, `SENDER_PHONE`, `LINKEDIN_URL`, `PORTFOLIO_URL` : déjà
  pré-remplis avec tes infos, à ajuster si besoin.
- `ANTHROPIC_API_KEY` (optionnel) : si tu as une clé API Anthropic, la lettre
  sera générée par Claude (texte plus varié à chaque envoi). Sinon, un
  template pré-écrit et déjà personnalisé (stage Nouvelair, FuelTrack, points
  forts) est utilisé — **aucune clé n'est nécessaire pour que l'appli
  fonctionne**.

## 3. Ton CV (FR et EN)

Ton CV anglais est déjà dans `cv/CV_EN.pdf`. L'appli te permet de choisir la
langue de la lettre **et** la langue du CV joint à chaque envoi :

- Ajoute ta version française sous `cv/CV_FR.pdf` pour pouvoir sélectionner
  "Français" côté CV (sinon l'appli enverra automatiquement celui qui existe,
  quel que soit le choix fait dans le formulaire).
- Tu peux changer les noms/emplacements via `CV_PATH_FR` et `CV_PATH_EN`
  dans `.env`.

## 3bis. Intitulé de poste

Le poste utilisé dans l'objet et le corps du mail est configurable dans
`.env` (`POSTE_FR` / `POSTE_EN`), par défaut : "Data Scientist / IA - ML
Engineer".

## 4. Lancer l'application

```bash
python app.py
```

Ouvre ensuite **http://127.0.0.1:5000** dans ton navigateur. Remplis le nom
de la société, l'email, choisis les langues, clique sur "Envoyer la
candidature".

## 5. Personnaliser la lettre

Le texte par défaut est dans `app.py`, variables `TEMPLATE_FR` / `TEMPLATE_EN`.
Il décrit déjà ton stage chez Nouvelair Tunisie (FuelTrack : modèles
prédictifs, module RAG, architecture full-stack, méthodologie SCRUM +
CRISP-DM) et tes points forts pour un recruteur (double compétence data
science / full-stack, GenAI/RAG, autonomie, apprentissage rapide). Tu peux
l'ajuster directement si tu veux mettre en avant d'autres projets selon le
poste visé.

## Limites à connaître

- Certains fournisseurs email bloquent l'envoi automatisé au-delà d'un
  certain volume/jour (Gmail : ~500 mails/jour max sur un compte perso). Pour
  une campagne de candidatures ciblées, ce n'est pas un problème.
- Vérifie toujours les adresses avant envoi : aucun contrôle de validité
  d'email n'est fait par l'appli.
- Reste raisonnable dans le nombre d'envois par jour pour éviter d'être
  marqué comme spam par ta boîte mail.
