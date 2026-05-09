import json
import os
from datetime import datetime

# ==================== CONSTANTES ====================

FICHIER_DONNEES = "sessions_ow.json"

HEROES = [
    # DPS
    "Sojourn", "Tracer", "Genji", "Soldier 76", "Cassidy",
    "Ashe", "Pharah", "Echo", "Hanzo", "Widowmaker",
    "Reaper", "Symmetra", "Torbjorn", "Bastion", "Mei",
    "Junkrat", "Sombra", "Venture", "Freja", "Vendetta",
    "Autre DPS",
    # SUPPORT
    "Ana", "Mercy", "Moira", "Lucio", "Zenyatta",
    "Baptiste", "Kiriko", "Lifeweaver", "Illari", "Juno",
    "Wuyang", "Mizuki", "Autre Support",
    # TANK
    "Reinhardt", "Winston", "D.Va", "Orisa", "Zarya",
    "Roadhog", "Junker Queen", "Ramattra", "Mauga",
    "Doomfist", "Hazard", "Jetpack Cat", "Autre Tank"
]

MODES = ["Escorte", "Contrôle", "Hybride", "Poussée", "Clash", "Flashpoint"]

QUESTIONS = [
    # POSITIONING
    ("isole", "POSITIONING — Tu t'es retrouvé isolé de ton équipe ?", ["Souvent", "Parfois", "Jamais"]),
    ("degats_dos", "POSITIONING — Tu as pris des dégâts dans le dos ?", ["Souvent", "Parfois", "Jamais"]),
    ("premiere_ligne", "POSITIONING — Tu étais en première ligne hors de ton rôle ?", ["Souvent", "Parfois", "Jamais"]),
    ("distance_tank", "POSITIONING — Tu respectais la bonne distance par rapport à ton tank ?", ["Toujours", "Parfois", "Jamais"]),
    ("cover", "POSITIONING — Tu utilisais les couverts disponibles ?", ["Toujours", "Parfois", "Jamais"]),

    # DÉCISIONS
    ("engage_evite", "DÉCISIONS — Tu as engagé des fights à éviter ?", ["Souvent", "Parfois", "Jamais"]),
    ("engage_rate", "DÉCISIONS — Tu as raté des fenêtres d'engagement favorables ?", ["Souvent", "Parfois", "Jamais"]),
    ("suivi_cible", "DÉCISIONS — Tu as suivi une cible en oubliant l'objectif ?", ["Souvent", "Parfois", "Jamais"]),
    ("ultime_gaspille", "DÉCISIONS — Tu as gaspillé ton ultime sans impact réel ?", ["Souvent", "Parfois", "Jamais"]),
    ("ultime_timing", "DÉCISIONS — Tu mourais avec ton ultime en poche ?", ["Souvent", "Parfois", "Jamais"]),

    # GAME SENSE
    ("connaissance_ennemis", "GAME SENSE — Tu savais où étaient les ennemis la plupart du temps ?", ["Toujours", "Parfois", "Jamais"]),
    ("surpris_flankers", "GAME SENSE — Tu as été surpris par des flankers ?", ["Souvent", "Parfois", "Jamais"]),
    ("lecture_ultime", "GAME SENSE — Tu anticipais les ultimes ennemis ?", ["Toujours", "Parfois", "Jamais"]),
    ("minimap", "GAME SENSE — Tu consultais régulièrement la mini-map ?", ["Toujours", "Parfois", "Jamais"]),
    ("rotation", "GAME SENSE — Tu effectuais les bonnes rotations sur l'objectif ?", ["Toujours", "Parfois", "Jamais"]),

    # MÉCANIQUES
    ("abilities", "MÉCANIQUES — Tu utilisais tes abilities au bon moment ?", ["Toujours", "Parfois", "Jamais"]),
    ("cooldown", "MÉCANIQUES — Tu gérais bien tes cooldowns (pas de double utilisation inutile) ?", ["Toujours", "Parfois", "Jamais"]),
    ("aim", "MÉCANIQUES — Ton aim te semblait précis et fluide ?", ["Toujours", "Parfois", "Jamais"]),

    # MENTAL / RYTHME
    ("tilt", "MENTAL — Tu as tilté après une défaite ou une mauvaise action ?", ["Souvent", "Parfois", "Jamais"]),
    ("communication", "MENTAL — Tu communiquais efficacement avec ton équipe ?", ["Toujours", "Parfois", "Jamais"]),
    ("respect_roles", "MENTAL — Tu respectais le rôle de chaque héros dans ta compo ?", ["Toujours", "Parfois", "Jamais"]),

    # RÉSULTAT
    ("resultat", "RÉSULTAT — Résultat de la partie ?", ["Victoire", "Défaite"]),
]

DIAGNOSTICS = {
    # POSITIONING
    "isole": ("Souvent", "❌ POSITIONING — Tu t'exposes trop seul. Reste toujours à portée visuelle de ton équipe avant d'avancer."),
    "degats_dos": ("Souvent", "❌ POSITIONING — Angles arrière non surveillés. Colle un mur dans ton dos avant chaque fight."),
    "premiere_ligne": ("Souvent", "❌ POSITIONING — Tu joues hors de ton rôle. Respecte ta distance optimale selon ton héros."),
    "distance_tank": ("Jamais", "❌ POSITIONING — Tu ne suis pas ton tank. Il est ton bouclier — reste dans son sillage."),
    "cover": ("Jamais", "❌ POSITIONING — Tu n'utilises pas les couverts. Avance de cover en cover, ne reste jamais à découvert."),

    # DÉCISIONS
    "engage_evite": ("Souvent", "❌ DÉCISIONS — Over-aggression. Demande-toi avant chaque engage : est-ce que je gagne ce fight ?"),
    "engage_rate": ("Souvent", "❌ DÉCISIONS — Tu rates tes fenêtres. Quand ton tank engage, c'est le signal — réagis immédiatement."),
    "suivi_cible": ("Souvent", "❌ DÉCISIONS — Tu chasses les kills au détriment de l'objectif. L'objectif prime toujours sur les eliminations."),
    "ultime_gaspille": ("Souvent", "❌ DÉCISIONS — Ultimes gaspillés. Utilise ton ultime uniquement quand 2+ ennemis sont groupés ou vulnérables."),
    "ultime_timing": ("Souvent", "❌ DÉCISIONS — Tu meurs avec ton ultime. Si tu sens le danger, utilise-le avant de mourir — un ultime mort = zéro impact."),

    # GAME SENSE
    "connaissance_ennemis": ("Jamais", "❌ GAME SENSE — Awareness insuffisant. Regarde la mini-map toutes les 5 secondes et note les absences ennemies."),
    "surpris_flankers": ("Souvent", "❌ GAME SENSE — Flancs non surveillés. Avant chaque fight identifie les angles de flanc possibles."),
    "lecture_ultime": ("Jamais", "❌ GAME SENSE — Tu n'anticipes pas les ultimes. Compte les ultimes ennemis et recule dès qu'un ultime de zone arrive."),
    "minimap": ("Jamais", "❌ GAME SENSE — Mini-map négligée. Force-toi à regarder la mini-map après chaque kill ou mort."),
    "rotation": ("Jamais", "❌ GAME SENSE — Mauvaises rotations. Anticipe les rotations adverses et prends position avant eux."),

    # MÉCANIQUES
    "abilities": ("Jamais", "❌ MÉCANIQUES — Abilities mal utilisées. Garde tes abilities défensives pour les vrais dangers, pas pour le confort."),
    "cooldown": ("Jamais", "❌ MÉCANIQUES — Mauvaise gestion des cooldowns. Ne double-utilise jamais une ability — attends que la situation le justifie vraiment."),
    "aim": ("Jamais", "❌ MÉCANIQUES — Aim imprécis. Fais 10 minutes d'échauffement aim avant de jouer en ranked."),

    # MENTAL
    "tilt": ("Souvent", "❌ MENTAL — Tu tiles facilement. Après une mauvaise action, respire et recentre-toi sur la prochaine décision uniquement."),
    "communication": ("Jamais", "❌ MENTAL — Communication absente. Un simple 'je dive', 'ultime prêt', 'repli' change radicalement la coordination."),
    "respect_roles": ("Jamais", "❌ MENTAL — Rôles non respectés. Connais le rôle de chaque héros dans ta compo et joue en fonction."),
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


def choisir_dans_liste(liste, titre):
    print(f"\n=== {titre} ===")
    for i, element in enumerate(liste, 1):
        print(f"  {i}. {element}")
    while True:
        choix = input("Ton choix : ")
        if choix.isdigit() and 1 <= int(choix) <= len(liste):
            return liste[int(choix) - 1]
        print("Choix invalide, recommence.")


def poser_questions():
    hero = choisir_dans_liste(HEROES, "QUEL HÉROS AS-TU JOUÉ ?")
    mode = choisir_dans_liste(MODES, "QUEL MODE DE JEU ?")

    reponses = {}
    print("\n=== RÉPONDS HONNÊTEMENT — C'EST POUR TA PROGRESSION ===\n")

    categorie_actuelle = ""
    for cle, question, reponses_possibles in QUESTIONS:
        categorie = question.split("—")[0].strip()
        if categorie != categorie_actuelle:
            categorie_actuelle = categorie
            print(f"\n{'─'*45}")
            print(f"  {categorie_actuelle}")
            print(f"{'─'*45}")

        print(f"\n👉 {question.split('—')[1].strip()}")
        for i, rep in enumerate(reponses_possibles, 1):
            print(f"   {i}. {rep}")
        while True:
            choix = input("   Ton choix : ")
            if choix.isdigit() and 1 <= int(choix) <= len(reponses_possibles):
                reponses[cle] = reponses_possibles[int(choix) - 1]
                break
            print("   Choix invalide, recommence.")

    reponses["hero"] = hero
    reponses["mode"] = mode
    reponses["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return reponses


def analyser_session(reponses):
    diagnostics = []
    for cle, (condition, message) in DIAGNOSTICS.items():
        if reponses.get(cle) == condition:
            diagnostics.append(message)
    if not diagnostics:
        diagnostics.append("✅ Excellente partie — aucun problème majeur détecté. Continue comme ça !")
    return diagnostics


def afficher_diagnostic(reponses, diagnostics):
    print("\n" + "="*45)
    print(f"  📊 DIAGNOSTIC OVERWATCH")
    print(f"  Héros : {reponses['hero']} | Mode : {reponses['mode']}")
    print(f"  Date : {reponses['date']} | Résultat : {reponses['resultat']}")
    print("="*45)

    categories = {}
    for d in diagnostics:
        if "—" in d:
            cat = d.split("—")[0].replace("❌", "").strip()
            categories.setdefault(cat, []).append(d.split("—")[1].strip())
        else:
            categories.setdefault("INFO", []).append(d)

    for cat, messages in categories.items():
        print(f"\n  [{cat}]")
        for msg in messages:
            print(f"  → {msg}")

    print("\n" + "="*45 + "\n")


def afficher_patterns(sessions):
    if not sessions:
        print("\n  Aucune session enregistrée pour l'instant.\n")
        return

    total = len(sessions)
    victoires = sum(1 for s in sessions if s["reponses"].get("resultat") == "Victoire")
    winrate = round((victoires / total) * 100)

    print("\n" + "="*45)
    print("  📈 TES PATTERNS OVERWATCH")
    print("="*45)
    print(f"  Sessions : {total} | Victoires : {victoires} | Défaites : {total - victoires}")
    print(f"  Winrate global : {winrate}%")

    # Héros les plus joués
    heroes_joues = {}
    for s in sessions:
        h = s["reponses"].get("hero", "Inconnu")
        heroes_joues[h] = heroes_joues.get(h, 0) + 1
    top_heroes = sorted(heroes_joues.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"\n  🎮 Héros les plus joués :")
    for h, nb in top_heroes:
        print(f"  → {h} ({nb} parties)")

    # Winrate par héros
    print(f"\n  🏆 Winrate par héros :")
    stats_heroes = {}
    for s in sessions:
        h = s["reponses"].get("hero", "Inconnu")
        if h not in stats_heroes:
            stats_heroes[h] = {"total": 0, "victoires": 0}
        stats_heroes[h]["total"] += 1
        if s["reponses"].get("resultat") == "Victoire":
            stats_heroes[h]["victoires"] += 1
    for h, stats in sorted(stats_heroes.items(), key=lambda x: x[1]["total"], reverse=True)[:5]:
        wr = round((stats["victoires"] / stats["total"]) * 100)
        print(f"  → {h} : {wr}% ({stats['total']} parties)")

    # Top 3 erreurs récurrentes
    print(f"\n  🔁 Tes 3 erreurs les plus fréquentes :")
    compteur = {}
    for s in sessions:
        for cle, (condition, message) in DIAGNOSTICS.items():
            if s["reponses"].get(cle) == condition:
                compteur[message] = compteur.get(message, 0) + 1
    if compteur:
        triees = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:3]
        for message, nb in triees:
            print(f"  → {message.split('—')[1].strip() if '—' in message else message} ({nb}x)")
    else:
        print("  Aucune erreur récurrente. 💪")

    print("="*45 + "\n")


def menu():
    print("\n" + "="*45)
    print("    🎮 TRACKER OVERWATCH — GAME SENSE")
    print("="*45)

    sessions = charger_donnees()

    while True:
        print(f"\n  Sessions enregistrées : {len(sessions)}")
        print("  1. Nouvelle session")
        print("  2. Voir mes patterns")
        print("  3. Quitter")
        choix = input("\n  Ton choix : ")

        if choix == "1":
            reponses = poser_questions()
            diagnostics = analyser_session(reponses)
            afficher_diagnostic(reponses, diagnostics)
            sessions.append({
                "date": reponses["date"],
                "hero": reponses["hero"],
                "mode": reponses["mode"],
                "reponses": reponses,
                "diagnostics": diagnostics
            })
            sauvegarder_donnees(sessions)
            print("  ✅ Session sauvegardée !\n")

        elif choix == "2":
            afficher_patterns(sessions)

        elif choix == "3":
            print("\n  À bientôt ! Continue de progresser sur Overwatch. 🚀\n")
            break

        else:
            print("  Choix invalide, recommence.")


# ==================== POINT D'ENTRÉE ====================

if __name__ == "__main__":
    menu()