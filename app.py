from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tracker_ow_secret_2026"

FICHIER_DONNEES = os.path.join(os.path.dirname(__file__), "donnees.json")

# ==================== CLASSIFICATION DES HÉROS ====================

HEROES_PAR_SPECIALISATION = {
    "tank_dive": ["Winston", "D.Va", "Doomfist", "Hazard", "Mauga", "Wrecking Ball"],
    "tank_defensif": ["Reinhardt", "Sigma", "Ramattra"],
    "tank_brawl": ["Junker Queen", "Zarya", "Roadhog", "Orisa"],
    "dps_hitscan": ["Sojourn", "Soldier 76", "Cassidy", "Widowmaker", "Ashe", "Freja", "Vendetta"],
    "dps_flanker": ["Tracer", "Genji", "Sombra", "Reaper"],
    "dps_projectile": ["Pharah", "Echo", "Junkrat", "Mei", "Hanzo", "Symmetra", "Bastion", "Torbjorn", "Venture"],
    "support_heal": ["Ana", "Mercy", "Moira", "Baptiste", "Lifeweaver", "Wuyang"],
    "support_utilitaire": ["Lucio", "Zenyatta", "Kiriko", "Illari", "Juno", "Mizuki", "Jetpack Cat"],
}

ROLES = {
    "tank_dive": "Tank", "tank_defensif": "Tank", "tank_brawl": "Tank",
    "dps_hitscan": "DPS", "dps_flanker": "DPS", "dps_projectile": "DPS",
    "support_heal": "Support", "support_utilitaire": "Support",
}

MODES = ["Escorte", "Contrôle", "Hybride", "Poussée", "Clash", "Flashpoint"]

# ==================== QUESTIONS ====================

QUESTIONS_COMMUNES = [
    ("comm_objectif", "Tu te concentrais sur l'objectif plutôt que sur les kills ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_rotation", "Tu effectuais les bonnes rotations sur la map ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_minimap", "Tu consultais régulièrement la mini-map ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_flankers", "Tu anticipais les flankers ennemis ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_tilt", "Tu gardais ton calme après les erreurs ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_communication", "Tu communiquais avec ton équipe ?", ["Toujours", "Parfois", "Jamais"]),
]

QUESTIONS_PAR_ROLE = {
    "Tank": [
        ("role_espace", "Tu créais suffisamment d'espace pour tes DPS et supports ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_peel", "Tu protégeais tes supports quand ils étaient attaqués ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_tempo", "Tu dictais le tempo du fight ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_ultime_tank", "Tu coordonnais ton ultime avec l'équipe ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_reset", "Tu savais quand reculer pour reset le fight ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "DPS": [
        ("role_cible", "Tu ciblais les bonnes cibles en priorité ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_positioning_dps", "Tu maintenais un bon positionnement offensif ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_ultime_dps", "Tu utilisais ton ultime au bon moment ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_suivi_tank", "Tu suivais l'engage de ton tank immédiatement ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_cooldowns_dps", "Tu gérais bien tes cooldowns offensifs ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "Support": [
        ("role_heal_priorite", "Tu healais les bonnes cibles en priorité ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_survie_support", "Tu survivais assez longtemps pour être utile ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_ultime_support", "Tu utilisais ton ultime de façon impactante ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_positioning_support", "Tu maintenais une bonne distance par rapport aux combats ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_awareness_support", "Tu anticipais les besoins de ton équipe ?", ["Toujours", "Parfois", "Jamais"]),
    ],
}

QUESTIONS_PAR_SPECIALISATION = {
    "tank_dive": [
        ("spec_cible_dive", "Tu ciblais les bons ennemis pendant ton dive ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_timing_dive", "Tu timais bien tes dives ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_sortie_dive", "Tu savais quand sortir d'un dive mal engagé ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cooldowns_dive", "Tu utilisais tes cooldowns de mobilité intelligemment ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "tank_defensif": [
        ("spec_bouclier", "Tu positionnais bien ton bouclier pour protéger l'équipe ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_angle_defensif", "Tu choisissais bien tes angles d'engage ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_pression", "Tu maintenais une pression constante sur l'objectif ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_timing_charge", "Tu timais bien tes charges/engages décisifs ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "tank_brawl": [
        ("spec_resource_brawl", "Tu gérais bien ta ressource principale ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_fight_brawl", "Tu choisissais bien tes fights ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_dos_brawl", "Tu faisais attention à ne pas être pris à revers ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_combo_brawl", "Tu combinais bien tes abilities ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "dps_hitscan": [
        ("spec_aim", "Ton aim était précis et consistant ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cover_hitscan", "Tu utilisais les couverts pour peek et te protéger ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_angle_hitscan", "Tu choisissais de bons angles de tir ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cible_hitscan", "Tu priorisais les cibles à haute valeur ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "dps_flanker": [
        ("spec_timing_flanker", "Tu timais bien tes flancs ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_survie_flanker", "Tu savais te désengager quand le flanc échouait ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cible_flanker", "Tu ciblais les supports ennemis en priorité ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cooldowns_flanker", "Tu gardais un cooldown de survie en réserve ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "dps_projectile": [
        ("spec_lead", "Tu anticipais bien le déplacement des ennemis ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_zone_projectile", "Tu utilisais tes abilities pour contrôler des zones ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_distance_projectile", "Tu maintenais la bonne distance selon ton héros ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_combo_projectile", "Tu combinais tes abilities pour maximiser les dégâts ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "support_heal": [
        ("spec_heal_continu", "Tu maintenais un heal continu sans interruption inutile ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_ressource_heal", "Tu gérais bien ta ressource de soin ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_boost", "Tu utilisais tes boosts au bon moment ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_antiheal", "Tu utilisais l'anti-heal au bon moment ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "support_utilitaire": [
        ("spec_utilite", "Tu maximisais ton utilité ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_peel_utilitaire", "Tu te défendais seul contre les ennemis qui te ciblaient ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_positioning_utilitaire", "Tu positionnais bien pour maximiser l'impact de tes abilities ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_aggression_utilitaire", "Tu alternais entre soutien et pression offensive ?", ["Toujours", "Parfois", "Jamais"]),
    ],
}

QUESTION_RESULTAT = ("resultat", "Résultat global de la session ?", ["Victoire majoritaire", "Partagé", "Défaite majoritaire"])

# ==================== DIAGNOSTICS ====================

DIAGNOSTICS_COMMUNS = {
    "comm_objectif": ("Jamais", "Tu chasses les kills plutôt que l'objectif. L'objectif prime toujours."),
    "comm_rotation": ("Jamais", "Tes rotations sont mauvaises. Anticipe les mouvements adverses."),
    "comm_minimap": ("Jamais", "Tu ignores la mini-map. Regarde-la après chaque kill ou mort."),
    "comm_flankers": ("Jamais", "Tu te fais surprendre. Identifie les angles de flanc avant chaque fight."),
    "comm_tilt": ("Jamais", "Tu tiles facilement. Recentre-toi sur la prochaine décision uniquement."),
    "comm_communication": ("Jamais", "Communication absente. 'Ultime prêt', 'je dive', 'repli' changent tout."),
}

DIAGNOSTICS_PAR_ROLE = {
    "Tank": {
        "role_espace": ("Jamais", "Tu ne crées pas d'espace. Ton rôle est d'occuper l'ennemi pour libérer tes alliés."),
        "role_peel": ("Jamais", "Tu ne protèges pas tes supports. Un support mort = fights perdus."),
        "role_tempo": ("Jamais", "Tu ne dictes pas le tempo. C'est toi qui decides quand engager et reculer."),
        "role_ultime_tank": ("Jamais", "Ultimes non coordonnés. Annonce ton ultime avant de l'utiliser."),
        "role_reset": ("Jamais", "Tu ne recules pas assez. Savoir reset un fight perdu est crucial."),
    },
    "DPS": {
        "role_cible": ("Jamais", "Tu tires sur n'importe qui. Priorise : support → DPS isolé → tank."),
        "role_positioning_dps": ("Jamais", "Ton positionnement t'expose trop. Avance de cover en cover."),
        "role_ultime_dps": ("Jamais", "Ultimes gaspillés. Utilise-les quand 2+ ennemis sont vulnérables."),
        "role_suivi_tank": ("Jamais", "Tu ne suis pas ton tank. Quand il engage, réagis immédiatement."),
        "role_cooldowns_dps": ("Jamais", "Garde toujours un cooldown défensif en réserve."),
    },
    "Support": {
        "role_heal_priorite": ("Jamais", "Tu heales dans le mauvais ordre. Priorité : tank → DPS en danger → autres."),
        "role_survie_support": ("Jamais", "Tu meurs trop vite. Ta survie est ta première priorité."),
        "role_ultime_support": ("Jamais", "Utilise tes ultimes pour contrer les ultimes ennemis ou sauver des fights."),
        "role_positioning_support": ("Jamais", "Tu es trop proche des combats. Reste à distance maximale utile."),
        "role_awareness_support": ("Jamais", "Tu réagis trop tard. Anticipe les besoins avant que la vie soit dans le rouge."),
    },
}

DIAGNOSTICS_PAR_SPECIALISATION = {
    "tank_dive": {
        "spec_cible_dive": ("Jamais", "Tu dives sur les mauvaises cibles. Vise les supports ou DPS isolés, jamais le tank."),
        "spec_timing_dive": ("Jamais", "Tes dives sont mal timés. Dive seulement quand ton équipe peut convertir."),
        "spec_sortie_dive": ("Jamais", "Tu restes trop longtemps dans un dive raté. Sors immédiatement si personne ne suit."),
        "spec_cooldowns_dive": ("Jamais", "Tu gaspilles ta mobilité. Garde un cooldown de sortie avant chaque dive."),
    },
    "tank_defensif": {
        "spec_bouclier": ("Jamais", "Ton bouclier est mal positionné. Il doit couvrir ton équipe, pas juste toi."),
        "spec_angle_defensif": ("Jamais", "Tu choisis de mauvais angles. Force l'ennemi à venir à toi."),
        "spec_pression": ("Jamais", "Tu ne maintiens pas la pression. Avance progressivement sur l'objectif."),
        "spec_timing_charge": ("Jamais", "Tes charges sont mal timées. Attends que l'ennemi soit groupé ou distrait."),
    },
    "tank_brawl": {
        "spec_resource_brawl": ("Jamais", "Tu gaspilles ta ressource principale. Gère-la comme une ultime."),
        "spec_fight_brawl": ("Jamais", "Tu prends de mauvais fights. Joue dans les espaces fermés à courte distance."),
        "spec_dos_brawl": ("Jamais", "Tu te fais prendre à revers. Positionne-toi dos à un mur."),
        "spec_combo_brawl": ("Jamais", "Enchaîne tes abilities dans le bon ordre pour maximiser les dégâts."),
    },
    "dps_hitscan": {
        "spec_aim": ("Jamais", "Ton aim est inconsistant. Fais 10 minutes d'échauffement avant chaque session."),
        "spec_cover_hitscan": ("Jamais", "Tu ne utilises pas les couverts. Peek → tire → retourne en cover."),
        "spec_angle_hitscan": ("Jamais", "Cherche les angles élevés et inattendus qui surprennent l'adversaire."),
        "spec_cible_hitscan": ("Jamais", "Cherche toujours le support ennemi ou la cible la plus dangereuse."),
    },
    "dps_flanker": {
        "spec_timing_flanker": ("Jamais", "Attends que l'ennemi soit engagé sur ton équipe avant de flanker."),
        "spec_survie_flanker": ("Jamais", "Si le flanc échoue, recule immédiatement — ne force pas."),
        "spec_cible_flanker": ("Jamais", "Un support éliminé en flanc peut retourner tout un fight."),
        "spec_cooldowns_flanker": ("Jamais", "Garde toujours un escape pour sortir si ça tourne mal."),
    },
    "dps_projectile": {
        "spec_lead": ("Jamais", "Anticipe le déplacement ennemi — tire où ils vont, pas où ils sont."),
        "spec_zone_projectile": ("Jamais", "Tes abilities servent à contrôler l'espace — utilise-les stratégiquement."),
        "spec_distance_projectile": ("Jamais", "Chaque héros projectile a une distance optimale — respecte-la."),
        "spec_combo_projectile": ("Jamais", "Enchaîne tes abilities dans le bon ordre pour burst les cibles."),
    },
    "support_heal": {
        "spec_heal_continu": ("Jamais", "Maintiens un heal constant sans laisser tes alliés descendre trop bas."),
        "spec_ressource_heal": ("Jamais", "Anticipe les besoins pour ne jamais tomber à court au mauvais moment."),
        "spec_boost": ("Jamais", "Réserve tes boosts pour les moments décisifs — engage tank, ultime DPS clé."),
        "spec_antiheal": ("Jamais", "L'anti-heal est souvent plus impactant que le heal — utilise-le sur les supports ennemis."),
    },
    "support_utilitaire": {
        "spec_utilite": ("Jamais", "Speed boost, discord, téléport — ces abilities doivent être actives en permanence."),
        "spec_peel_utilitaire": ("Jamais", "Tu dois pouvoir survivre aux flankers sans aide — travaille ton peel."),
        "spec_positioning_utilitaire": ("Jamais", "Place-toi là où tes abilities touchent le maximum d'alliés."),
        "spec_aggression_utilitaire": ("Jamais", "Les supports utilitaires doivent alterner entre soutien et pression offensive."),
    },
}

# ==================== UTILITAIRES ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_specialisation(hero):
    for spec, heroes in HEROES_PAR_SPECIALISATION.items():
        if hero in heroes:
            return spec
    return None

def get_role(hero):
    spec = get_specialisation(hero)
    return ROLES.get(spec) if spec else None

def get_all_heroes():
    all_heroes = []
    for heroes in HEROES_PAR_SPECIALISATION.values():
        all_heroes.extend(heroes)
    return sorted(set(all_heroes))

def charger_donnees():
    try:
        with open(FICHIER_DONNEES, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"profils": {}}

def sauvegarder_donnees(donnees):
    with open(FICHIER_DONNEES, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)

def get_profil(pseudo):
    donnees = charger_donnees()
    return donnees["profils"].get(pseudo)

def get_questions_pour_hero(hero):
    spec = get_specialisation(hero)
    role = get_role(hero)
    questions = []
    if role:
        questions.extend(QUESTIONS_PAR_ROLE.get(role, []))
    if spec:
        questions.extend(QUESTIONS_PAR_SPECIALISATION.get(spec, []))
    return questions

def analyser_par_hero(hero, reponses):
    diagnostics = []
    spec = get_specialisation(hero)
    role = get_role(hero)

    for cle, (condition, message) in DIAGNOSTICS_COMMUNS.items():
        if reponses.get(cle) == condition:
            diagnostics.append(("Général", message))

    if role and role in DIAGNOSTICS_PAR_ROLE:
        for cle, (condition, message) in DIAGNOSTICS_PAR_ROLE[role].items():
            if reponses.get(f"{hero}_{cle}") == condition:
                diagnostics.append((role, message))

    if spec and spec in DIAGNOSTICS_PAR_SPECIALISATION:
        for cle, (condition, message) in DIAGNOSTICS_PAR_SPECIALISATION[spec].items():
            if reponses.get(f"{hero}_{cle}") == condition:
                diagnostics.append((spec.replace("_", " ").title(), message))

    if not diagnostics:
        diagnostics.append(("✅", f"Excellente session sur {hero} !"))

    return diagnostics

def calculer_stats_profil(sessions):
    if not sessions:
        return {}

    total = len(sessions)
    victoires = sum(1 for s in sessions if s.get("resultat") == "Victoire majoritaire")
    winrate = round((victoires / total) * 100)

    stats_heroes = {}
    for s in sessions:
        for hero in s.get("heroes", []):
            if hero not in stats_heroes:
                stats_heroes[hero] = {"total": 0, "victoires": 0}
            stats_heroes[hero]["total"] += 1
            if s.get("resultat") == "Victoire majoritaire":
                stats_heroes[hero]["victoires"] += 1

    for h in stats_heroes:
        stats_heroes[h]["winrate"] = round(
            (stats_heroes[h]["victoires"] / stats_heroes[h]["total"]) * 100
        )

    compteur_erreurs = {}
    for s in sessions:
        for hero, diags in s.get("diagnostics", {}).items():
            for cat, message in diags:
                if cat != "✅":
                    compteur_erreurs[message] = compteur_erreurs.get(message, 0) + 1

    top_erreurs = sorted(compteur_erreurs.items(), key=lambda x: x[1], reverse=True)[:5]

    sessions_par_date = {}
    for s in sessions:
        date = s.get("date", "")[:10]
        if date not in sessions_par_date:
            sessions_par_date[date] = {"total": 0, "victoires": 0}
        sessions_par_date[date]["total"] += 1
        if s.get("resultat") == "Victoire majoritaire":
            sessions_par_date[date]["victoires"] += 1

    progression = [
        {
            "date": date,
            "winrate": round((v["victoires"] / v["total"]) * 100),
            "sessions": v["total"]
        }
        for date, v in sorted(sessions_par_date.items())
    ]

    return {
        "total": total,
        "victoires": victoires,
        "winrate": winrate,
        "stats_heroes": stats_heroes,
        "top_erreurs": top_erreurs,
        "progression": progression,
    }

# ==================== ROUTES ====================

@app.route("/")
def index():
    donnees = charger_donnees()
    profils = donnees.get("profils", {})
    profils_liste = [
        {
            "pseudo": p["pseudo"],
            "sessions": len(p.get("sessions", [])),
            "date_creation": p.get("date_creation", "")
        }
        for p in profils.values()
    ]
    return render_template("index.html", profils=profils_liste)

@app.route("/login", methods=["GET", "POST"])
def login():
    erreur = None
    if request.method == "POST":
        action = request.form.get("action")
        pseudo = request.form.get("pseudo", "").strip()
        password = request.form.get("password", "")

        if not pseudo or not password:
            erreur = "Pseudo et mot de passe requis."
        else:
            donnees = charger_donnees()
            profils = donnees.get("profils", {})

            if action == "creer":
                if pseudo in profils:
                    erreur = "Ce pseudo est déjà pris."
                else:
                    profils[pseudo] = {
                        "pseudo": pseudo,
                        "password": hash_password(password),
                        "date_creation": datetime.now().strftime("%Y-%m-%d"),
                        "sessions": []
                    }
                    donnees["profils"] = profils
                    sauvegarder_donnees(donnees)
                    session["pseudo"] = pseudo
                    return redirect(url_for("dashboard"))

            elif action == "connexion":
                if pseudo not in profils:
                    erreur = "Profil introuvable."
                elif profils[pseudo]["password"] != hash_password(password):
                    erreur = "Mot de passe incorrect."
                else:
                    session["pseudo"] = pseudo
                    return redirect(url_for("dashboard"))

    return render_template("login.html", erreur=erreur)

@app.route("/dashboard")
def dashboard():
    if "pseudo" not in session:
        return redirect(url_for("index"))
    pseudo = session["pseudo"]
    profil = get_profil(pseudo)
    if not profil:
        return redirect(url_for("index"))
    sessions = profil.get("sessions", [])
    stats = calculer_stats_profil(sessions)
    return render_template("dashboard.html", pseudo=pseudo, stats=stats, nb_sessions=len(sessions))

@app.route("/deconnexion")
def deconnexion():
    session.clear()
    return redirect(url_for("index"))

@app.route("/questions", methods=["GET", "POST"])
def questions():
    if "pseudo" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        heroes_joues = request.form.getlist("heroes")
        mode = request.form.get("mode")
        if not heroes_joues:
            return redirect(url_for("questions"))
        session["heroes_joues"] = heroes_joues
        session["mode"] = mode
        session["current_hero_index"] = 0
        session["reponses_communes"] = {}
        session["reponses_par_hero"] = {}
        return redirect(url_for("questions_communes"))

    heroes_par_role = {
        "Tank": {
            "Dive": HEROES_PAR_SPECIALISATION["tank_dive"],
            "Défensif": HEROES_PAR_SPECIALISATION["tank_defensif"],
            "Brawl": HEROES_PAR_SPECIALISATION["tank_brawl"],
        },
        "DPS": {
            "Hitscan": HEROES_PAR_SPECIALISATION["dps_hitscan"],
            "Flanker": HEROES_PAR_SPECIALISATION["dps_flanker"],
            "Projectile": HEROES_PAR_SPECIALISATION["dps_projectile"],
        },
        "Support": {
            "Heal Principal": HEROES_PAR_SPECIALISATION["support_heal"],
            "Utilitaire": HEROES_PAR_SPECIALISATION["support_utilitaire"],
        },
    }
    return render_template("questions.html", heroes_par_role=heroes_par_role, modes=MODES)

@app.route("/questions/communes", methods=["GET", "POST"])
def questions_communes():
    if "pseudo" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        reponses = {}
        for cle, _, _ in QUESTIONS_COMMUNES:
            reponses[cle] = request.form.get(cle)
        reponses[QUESTION_RESULTAT[0]] = request.form.get(QUESTION_RESULTAT[0])
        session["reponses_communes"] = reponses
        session["current_hero_index"] = 0
        return redirect(url_for("questions_hero"))

    return render_template("questions_communes.html",
                           questions=QUESTIONS_COMMUNES,
                           question_resultat=QUESTION_RESULTAT,
                           heroes=session.get("heroes_joues", []))

@app.route("/questions/hero", methods=["GET", "POST"])
def questions_hero():
    if "pseudo" not in session:
        return redirect(url_for("index"))

    heroes_joues = session.get("heroes_joues", [])
    index = session.get("current_hero_index", 0)

    if index >= len(heroes_joues):
        return redirect(url_for("diagnostic"))

    hero = heroes_joues[index]
    questions_hero_list = get_questions_pour_hero(hero)

    if request.method == "POST":
        reponses_par_hero = session.get("reponses_par_hero", {})
        reponses_hero = {}
        for cle, _, _ in questions_hero_list:
            reponses_hero[f"{hero}_{cle}"] = request.form.get(cle)
        reponses_par_hero[hero] = reponses_hero
        session["reponses_par_hero"] = reponses_par_hero
        session["current_hero_index"] = index + 1
        return redirect(url_for("questions_hero"))

    spec = get_specialisation(hero)
    role = get_role(hero)
    return render_template("questions_hero.html",
                           hero=hero,
                           role=role,
                           spec=spec.replace("_", " ").title() if spec else "",
                           questions=questions_hero_list,
                           index=index + 1,
                           total=len(heroes_joues))

@app.route("/diagnostic")
def diagnostic():
    if "pseudo" not in session:
        return redirect(url_for("index"))

    pseudo = session["pseudo"]
    reponses_communes = session.get("reponses_communes", {})
    reponses_par_hero = session.get("reponses_par_hero", {})
    heroes_joues = session.get("heroes_joues", [])
    mode = session.get("mode", "")

    diagnostics_par_hero = {}
    for hero in heroes_joues:
        reponses_hero = reponses_par_hero.get(hero, {})
        reponses_totales = {**reponses_communes, **reponses_hero}
        diagnostics_par_hero[hero] = analyser_par_hero(hero, reponses_totales)

    resultat = reponses_communes.get("resultat", "")
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    nouvelle_session = {
        "date": date,
        "mode": mode,
        "heroes": heroes_joues,
        "resultat": resultat,
        "reponses_communes": reponses_communes,
        "reponses_par_hero": reponses_par_hero,
        "diagnostics": diagnostics_par_hero
    }

    donnees = charger_donnees()
    donnees["profils"][pseudo]["sessions"].append(nouvelle_session)
    sauvegarder_donnees(donnees)

    return render_template("diagnostic.html",
                           heroes=heroes_joues,
                           diagnostics_par_hero=diagnostics_par_hero,
                           resultat=resultat,
                           mode=mode,
                           date=date,
                           pseudo=pseudo)

@app.route("/progression")
def progression():
    if "pseudo" not in session:
        return redirect(url_for("index"))
    pseudo = session["pseudo"]
    profil = get_profil(pseudo)
    if not profil:
        return redirect(url_for("index"))
    sessions = profil.get("sessions", [])
    stats = calculer_stats_profil(sessions)
    return render_template("progression.html", pseudo=pseudo, stats=stats)

if __name__ == "__main__":
    app.run(debug=True)
