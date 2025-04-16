# 📊 Analyse des Cryptomonnaies

Ce projet permet d'analyser les performances et les risques de plusieurs cryptomonnaies (BTC, ETH, SOL, BNB) en produisant des indicateurs financiers, des matrices de corrélation, des graphiques de performance et un rapport HTML interactif.

---

## 📁 Structure du projet

. ├── app.py # Script principal à exécuter ├── analyze.py # Contient la fonction run_analysis() ├── generate.py # Contient la fonction generate_report() ├── extraction.py # Contient la fonction extract_data() ├── output/ # Dossier de sortie (automatiquement créé) └── README.md # Ce fichier


---

## ⚙️ Prérequis

Avant de commencer, assurez-vous d’avoir installé **Python 3.8 ou supérieur**.

### 📦 Librairies nécessaires

Voici les bibliothèques utilisées :

- `yfinance`
- `pandas`
- `numpy`
- `matplotlib`
- `seaborn`
- `fredapi`
- `base64`
- `json`
- `itertools`
- `io`
- `os`

---

## 🧪 Installation

1. **Clonez le dépôt :**

```bash
git clone <url_du_repository>
cd nom_du_dossier

2. **Créez un environnement virtuel (optionnel mais recommandé) :**
python3 -m venv env
source env/bin/activate  # Sur Windows: env\Scripts\activate


3. **Installez les dépendances :**
pip install -r requirements.txt

⚙️ Utilisation

1. Lancer l'application Flask
Dans le terminal, dans le dossier PYTHON_APP/ :

python app.py
L’application sera accessible à l’adresse http://127.0.0.1:5000

📤 Fonctionnement de l'application

L’utilisateur entre une liste de tickers crypto (ex : BTC, ETH, SOL, BNB)
L’application télécharge les données via yfinance
Les rendements sont calculés et sauvegardés dans output/rendements_cryptos.csv
Une matrice de corrélation est affichée et enregistrée sous forme d'image
Les fichiers générés (CSV, PNG) sont automatiquement organisés dans le dossier output/


🗂️ Bonnes pratiques

Ne pas modifier manuellement les fichiers dans output/, ils sont régénérés à chaque exécution.
Utiliser un environnement virtuel (venv) pour isoler les dépendances :
python -m venv venv
source venv/bin/activate  # ou .\venv\Scripts\activate sur Windows


👤 Auteur

Projet développé par Val--


