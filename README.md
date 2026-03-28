# Outil d’aide à la décision — Adéquation du prix d’un appartement

## Contexte
Ce projet propose une **mini-plateforme MLOps** de scoring immobilier.

Le cas de démonstration fourni concerne **Toulon centre-ville**, dans une zone d’intérêt définie via une **sélection de section cadastrale** (environ **15 minutes max à pied de la gare**).

L’objectif est de répondre rapidement à une question simple mais critique :  
*“le prix demandé est-il cohérent avec les caractéristiques du bien, dans cette zone ?”*

L’approche a été volontairement **simple, légère et efficace**, avec un **impact business immédiat** : une estimation de prix attendu, un écart en %, et un label lisible.

> Le projet de démonstration actuel est **Toulon**, mais la structure du code permet de reproduire la même démarche sur **d’autres villes / zones** via un **projet configuré**, sans modifier le code métier.

---

## Données utilisées (source officielle DVF)
Les données proviennent de la base officielle **DVF — Demande de Valeur Foncière** (transactions immobilières enregistrées).

Référence grand public (présentation DVF) :  
https://www.pricehubble.com/fr/blog/base-dvf-ventes-immobilieres-france

### Périmètre & filtres du projet de démonstration
L’extraction DVF a été filtrée selon :
- Département : **83 (Var)**
- Commune : **Toulon**
- **Section cadastrale sélectionnée** (centre-ville)
- `type_local = Appartement` (le reste est ignoré)

### Fenêtre temporelle (pourquoi uniquement la dernière année ?)
Même si DVF permet de remonter plus loin (jusqu’à ~2020 et avant), nous avons choisi de **n’utiliser que la dernière année disponible** :
- pour limiter les effets de rupture liés à la période **COVID** et aux changements de dynamique de marché,
- pour obtenir un signal **plus représentatif du marché actuel** et exploitable pour une décision imminente.

Dans ce projet, la période utilisée est :
- **01/05/2024 → 30/06/2025**

### Variables DVF exploitées
Colonnes utilisées pour l’estimation :
- `valeur_fonciere` (prix de transaction)
- `surface_reelle_bati` (surface)
- `nombre_pieces_principales` (nombre de pièces)
- `type_local` (filtré à Appartement)

---

## Ce que fait l’outil
L’utilisateur renseigne :
- **Prix (€)**
- **Surface (m²)**
- **Nombre de pièces**

L’API calcule puis renvoie :
- un **prix attendu** (`expected_price`) estimé à partir de ventes DVF comparables,
- un **ratio** (`price_ratio = price / expected_price`) et un **écart** (en € et en % dans l’UI),
- un **label** simple :
  - `underpriced` (prix sous l’attendu),
  - `fair` (prix cohérent),
  - `overpriced` (prix au-dessus de l’attendu),
- un **score** ∈ [0,1] (plus proche de 1 = plus proche du prix attendu).

L’interface web affiche :
- un **résumé** (“D’après les caractéristiques : ce logement est …”),
- la section **Why** (prix attendu, écart en €, écart en %, prix/m²),
- la **méthode** et la **source DVF**.

L’API principale est :

`GET /score?surface=...&nb_room=...&price=...&project=...`

Le paramètre `project` permet de sélectionner un **projet configuré** (par défaut : le projet actif défini dans la configuration).

---

## Méthode (maths, version courte et compréhensible)
### Modèle calibré sur de vraies ventes
Les paramètres du modèle (**b0, b1, b2**) ainsi que la variabilité **σ** ne sont pas choisis arbitrairement :
ils sont **estimés automatiquement** à partir de **transactions DVF réelles** (sur la zone et la période sélectionnées).

Concrètement :
- `train_model.py` lit le CSV DVF filtré,
- ajuste les coefficients par régression sur `log(prix)`,
- calcule `σ` à partir de la dispersion observée (résidus),
- sauvegarde le modèle entraîné dans un artifact JSON,
- l’API charge ensuite ce fichier pour scorer (inférence).

### Pourquoi utiliser le log du prix ?
On utilise `log(prix)` plutôt que `prix` car en immobilier on raisonne souvent en **pourcentages** :
- +20 000€ n’a pas le même sens sur 100 000€ que sur 500 000€.
Le log permet au modèle de mieux capter ces **écarts relatifs** et stabilise les variations.

### Score & label
- On estime un `prix_attendu` à partir des caractéristiques (surface, pièces).
- On mesure l’écart relatif au marché local via un écart normalisé (avec **σ**).
- Le score diminue quand on s’éloigne du prix attendu, et le label est basé sur le ratio :
  - `underpriced` si ratio < 0.9
  - `fair` si 0.9 ≤ ratio ≤ 1.1
  - `overpriced` si ratio > 1.1

### Robustesse statistique (intuition)
Après filtrage, le modèle est entraîné sur **n = 124** ventes (Appartements).  
Avec **n > 100**, on est dans un cadre où les estimations (moyennes/variabilité) deviennent généralement **stables** (intuition type **TCL**) : la dispersion `σ` est suffisamment informée pour normaliser les écarts de façon cohérente.

---

## Ce qui a été volontairement choisi de ne PAS faire
### 1) Historisation des recherches
- Pas de base de données
- Pas d’ID de recherche / nom de recherche
- Pas d’export Excel des historiques

> Amélioration possible : stocker les requêtes (ex: SQLite) avec un nom de recherche lié à un bien, et exporter en `.xlsx`.

### 2) Hébergement en ligne
- Pas de déploiement sur serveur (coût/ops)
- Pas de serveur MCP

> Amélioration possible : héberger l’application (container / cloud) pour garantir une disponibilité continue.

---

## Structure du projet
- `main.py` : API FastAPI
- `ui.py` : route UI (`/`) qui sert `static/index.html`
- `validation.py` : validation des inputs (HTTP 422)
- `score.py` : inférence (score / label)
- `model.py` : définition du modèle
- `model_loader.py` : chargement du modèle
- `project_config.py` : chargement de la configuration projet
- `train_model.py` : entraînement/calibration (offline) → génère l’artifact modèle
- `projects/` : projets configurés (ex. `toulon-centre/`)
- `static/index.html` : interface utilisateur
- `requirements.txt` : dépendances runtime API (**versionnées**)
- `requirements-train.txt` : dépendances entraînement (**versionnées**)
- `Dockerfile` : build & run container

---

## Installation & exécution (local)
### 1) Créer et activer l’environnement
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
```

### 2) Installer les dépendances API
```bash
python -m pip install -r requirements.txt
```

### 3) (Optionnel) Installer les dépendances training
```bash
python -m pip install -r requirements-train.txt
```

### 4) Entraîner / recalibrer le modèle (offline)
```bash
python train_model.py
```

### 5) Lancer l’API + UI
```bash
python -m uvicorn main:app --reload --port 8000
```

UI : http://127.0.0.1:8000/  
Docs : http://127.0.0.1:8000/docs  
API : http://127.0.0.1:8000/score?surface=50&nb_room=2&price=180000&project=toulon-centre

---

## Docker (test)
### Build
```bash
docker build -t fastapi-score .
```

### Run
```bash
docker run --rm -p 8001:8000 fastapi-score
```

UI : http://127.0.0.1:8001/  
Docs : http://127.0.0.1:8001/docs
---

## Cycle de vie du projet
Dans cette version, la mini-plateforme couvre déjà plusieurs étapes utiles :
- **entraînement offline** du modèle,
- **persistance** de l’artifact,
- **serving** via API/UI,
- **conteneurisation Docker**,
- **versionnement** des dépendances.

Améliorations futures possibles :
- déploiement continu pour garder le service disponible,
- gestion plus avancée des versions de modèles,
- monitoring et journalisation des usages.

---

## Auteur
Créé par **Lolita ABOA**.

Projet de démonstration : **Toulon centre-ville**.  
Profil : https://lolitadiamant.wixsite.com/data-en-herbe
