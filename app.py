from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tracker_ow_secret"

# ==================== CONSTANTES ====================

FICHIER_DONNEES = os.path.join(os.path.dirname(__file__), "sessions_ow.json")

HEROES = [
    "Sojourn", "Tracer", "Genji", "Soldier 76", "Cassidy",
    "Ashe", "Pharah", "Echo", "Hanzo", "Widowmaker",
    "Reaper", "Symmetra", "Torbjorn", "Bastion", "Mei",
    "Junkrat", "Sombra", "Venture", "Freja", "Vendetta",
    "Autre DPS",
    "Ana", "Mercy", "Moira", "Lucio", "Zenyatta",
    "Baptiste", "Kiriko", "Lifeweaver", "Illari", "Juno",
    "Wuyang", "Mizuki", "Autre Support",
    "Reinhardt", "Winston", "D.Va", "Orisa", "Zarya",
    "Roadhog", "Junker Queen", "Ramattra", "Mauga",
    "Doomfist", "Hazard", "Jetpack Cat", "Autre Tank"
]

MODES = ["Escorte", "Contrôle", "Hybride", "Poussée", "Clash", "Flashpoint"]

QUESTIONS = [
    ("isole", "Tu t'es retrouvé isolé de ton équipe ?", ["Souvent", "Parfois", "Jamais"]),
    ("degats_dos", "Tu as pris des dégâts dans le dos ?", ["Souvent", "Parfois", "Jamais"]),
    ("premiere_ligne", "Tu étais en première ligne hors de ton rôle ?", ["Souvent", "Parfois", "Jamais"]),
    ("distance_tank", "Tu respectais la bonne distance par rapport à ton tank ?", ["Toujours", "Parfois", "Jamais"]),
    ("cover", "Tu utilisais les couverts disponibles ?", ["Toujours", "Parfois", "Jamais"]),
    ("engage_evite", "Tu as engagé des fights à éviter ?", ["Souvent", "Parfois", "Jamais"]),
    ("engage_rate", "Tu as raté des fenêtres d'engagement favorables ?", ["Souvent", "Parfois", "Jamais"]),
    ("suivi_cible", "Tu as suivi une cible en oubliant l'objectif ?", ["Souvent", "Parfois", "Jamais"]),
    ("ultime_gaspille", "Tu as gaspillé ton ultime sans impact réel ?", ["Souvent", "Parfois", "Jamais"]),
    ("ultime_timing", "Tu mourais avec ton ultime en poche ?", ["Souvent", "Parfois", "Jamais"]),
    ("connaissance_ennemis", "Tu savais où étaient les ennemis la plupart du temps ?", ["Toujours", "Parfois", "Jamais"]),
    ("surpris_flankers", "Tu as été surpris par des flankers ?", ["Souvent", "Parfois", "Jamais"]),
    ("lecture_ultime", "Tu anticipais les ultimes ennemis ?", ["Toujours", "Parfois", "Jamais"]),
    ("minimap", "Tu consultais régulièrement la mini-map ?", ["Toujours", "Parfois", "Jamais"]),
    ("rotation", "Tu effectuais les bonnes rotations sur l'objectif ?", ["Toujours", "Parfois", "Jamais"]),
    ("abilities", "Tu utilisais tes abilities au bon moment ?", ["Toujours", "Parfois", "Jamais"]),
    ("cooldown", "Tu gérais bien tes cooldowns ?", ["Toujours", "Parfois", "Jamais"]),
    ("aim", "Ton aim te semblait précis et fluide ?", ["Toujours", "Parfois", "Jamais"]),
    ("tilt", "Tu as tilté après une défaite ou une mauvaise action ?", ["Souvent", "Parfois", "Jamais"]),
    ("communication", "Tu communiquais efficacement avec ton équipe ?", ["Toujours", "Parfois", "Jamais"]),
    ("respect_roles", "Tu respectais le rôle de chaque héros dans ta compo ?", ["Toujours", "Parfois", "Jamais"]),
    ("resultat", "Résultat de la partie ?", ["Victoire", "Défaite"]),
]

DIAGNOSTICS = {
    "isole": ("Souvent", "Tu t'exposes trop seul. Reste toujours à portée visuelle de ton équipe avant d'avancer."),
    "degats_dos": ("Souvent", "Angles arrière non surveillés. Colle un mur dans ton dos avant chaque fight."),
    "premiere_ligne": ("Souvent", "Tu joues hors de ton rôle. Respecte ta distance optimale selon ton héros."),
    "distance_tank": ("Jamais", "Tu ne suis pas ton tank. Il est ton bouclier — reste dans son sillage."),
    "cover": ("Jamais", "Tu n'utilises pas les couverts. Avance de cover en cover, ne reste jamais à découvert."),
    "engage_evite": ("Souvent", "Over-aggression. Demande-toi avant chaque engage : est-ce que je gagne ce fight ?"),
    "engage_rate": ("Souvent", "Tu rates tes fenêtres. Quand ton tank engage, c'est le signal — réagis immédiatement."),
    "suivi_cible": ("Souvent", "Tu chasses les kills au détriment de l'objectif. L'objectif prime toujours."),
    "ultime_gaspille": ("Souvent", "Ultimes gaspillés. Utilise ton ultime uniquement quand 2+ ennemis sont groupés."),
    "ultime_timing": ("Souvent", "Tu meurs avec ton ultime. Si tu sens le danger, utilise-le avant de mourir."),
    "connaissance_ennemis": ("Jamais", "Awareness insuffisant. Regarde la mini-map toutes les 5 secondes."),
    "surpris_flankers": ("Souvent", "Flancs non surveillés. Avant chaque fight identifie les angles de flanc possibles."),
    "lecture_ultime": ("Jamais", "Tu n'anticipes pas les ultimes. Compte-les et recule dès qu'un ultime de zone arrive."),
    "minimap": ("Jamais", "Mini-map négligée. Force-toi à regarder la mini-map après chaque kill ou mort."),
    "rotation": ("Jamais", "Mauvaises rotations. Anticipe les rotations adverses et prends position avant eux."),
    "abilities": ("Jamais", "Abilities mal utilisées. Garde tes abilities défensives pour les vrais dangers."),
    "cooldown": ("Jamais", "Mauvaise gestion des cooldowns. N'utilise jamais une ability deux fois de suite inutilement."),
    "aim": ("Jamais", "Aim imprécis. Fais 10 minutes d'échauffement aim avant de jouer en ranked."),
    "tilt": ("Souvent", "Tu tiles facilement. Après une mauvaise action, respire et recentre-toi sur la prochaine décision."),
    "communication": ("Jamais", "Communication absente. Un simple 'je dive', 'ultime prêt' change radicalement la coordination."),
    "respect_roles": ("Jamais", "Rôles non respectés. Connais le rôle de chaque héros dans ta compo et joue en fonction."),
}

# ==================== FONCTIONS ====================

def charger_donnees():
    try:
        with open(FICHIER_DONNEES, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def sauvegarder_donnees(sessions):
    with open(FICHIER_DONNEES, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=4, ensure_ascii=False)

def analyser_session(reponses):
    diagnostics = []
    for cle, (condition, message) in DIAGNOSTICS.items():
        if reponses.get(cle) == condition:
            diagnostics.append(message)
    if not diagnostics:
        diagnostics.append("Excellente partie — aucun problème majeur détecté. Continue comme ça !")
    return diagnostics

# ==================== ROUTES FLASK ====================

@app.route("/")
def index():
    sessions = charger_donnees()
    return render_template("index.html", total=len(sessions))

@app.route("/questions", methods=["GET", "POST"])
def questions():
    if request.method == "POST":
        reponses = {}
        reponses["hero"] = request.form.get("hero")
        reponses["mode"] = request.form.get("mode")
        reponses["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        for cle, _, _ in QUESTIONS:
            reponses[cle] = request.form.get(cle)
        diagnostics = analyser_session(reponses)
        session["last_reponses"] = reponses
        session["last_diagnostics"] = diagnostics
        sessions = charger_donnees()
        sessions.append({
            "date": reponses["date"],
            "hero": reponses["hero"],
            "mode": reponses["mode"],
            "reponses": reponses,
            "diagnostics": diagnostics
        })
        sauvegarder_donnees(sessions)
        return redirect(url_for("diagnostic"))
    return render_template("questions.html", heroes=HEROES, modes=MODES, questions=QUESTIONS)

@app.route("/diagnostic")
def diagnostic():
    reponses = session.get("last_reponses", {})
    diagnostics = session.get("last_diagnostics", [])
    return render_template("diagnostic.html", reponses=reponses, diagnostics=diagnostics)

@app.route("/patterns")
def patterns():
    sessions = charger_donnees()
    if not sessions:
        return render_template("patterns.html", vide=True)
    total = len(sessions)
    victoires = sum(1 for s in sessions if s["reponses"].get("resultat") == "Victoire")
    winrate = round((victoires / total) * 100)
    stats_heroes = {}
    for s in sessions:
        h = s["reponses"].get("hero", "Inconnu")
        if h not in stats_heroes:
            stats_heroes[h] = {"total": 0, "victoires": 0}
        stats_heroes[h]["total"] += 1
        if s["reponses"].get("resultat") == "Victoire":
            stats_heroes[h]["victoires"] += 1
    for h in stats_heroes:
        stats_heroes[h]["winrate"] = round((stats_heroes[h]["victoires"] / stats_heroes[h]["total"]) * 100)
    compteur = {}
    for s in sessions:
        for cle, (condition, message) in DIAGNOSTICS.items():
            if s["reponses"].get(cle) == condition:
                compteur[message] = compteur.get(message, 0) + 1
    top_erreurs = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:5]
    return render_template("patterns.html", vide=False, total=total,
                           victoires=victoires, winrate=winrate,
                           stats_heroes=stats_heroes, top_erreurs=top_erreurs)

# ==================== LANCEMENT ====================

if __name__ == "__main__":
    app.run(debug=True)