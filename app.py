from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tracker_ow_secret_2026"

# ==================== MONGODB ====================

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["tracker_overwatch"]
profils_col = db["profils"]

# ==================== CLASSIFICATION ====================

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
    ("comm_objectif", "L'objectif était ta priorité absolue, même quand tu avais une opportunité de kill ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_rotation", "Tu anticipais les rotations adverses et tu prenais position avant eux ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_minimap", "Tu regardais la mini-map régulièrement pour tracker les ennemis invisibles ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_flankers", "Tu savais à tout moment où étaient les flankers ennemis (Tracer, Genji, Sombra...) ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_tilt", "Après une erreur ou une mort frustrante, tu restais focus sur la prochaine décision ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_communication", "Tu callais les infos importantes à ton équipe (ultime prêt, flanker repéré, repli nécessaire) ?", ["Toujours", "Parfois", "Jamais"]),
    ("comm_ultime_tracking", "Tu trackais les ultimes ennemis pour anticiper les moments dangereux ?", ["Toujours", "Parfois", "Jamais"]),
]

QUESTIONS_PAR_ROLE = {
    "Tank": [
        ("role_espace", "Tes engages créaient un espace réel pour tes alliés — les ennemis étaient forcés de te deal ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_peel", "Quand ton Ana ou ton Zenyatta se faisait dive, tu abandonnais ton engage pour revenir le défendre ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_tempo", "C'est toi qui choisissais QUAND le fight commençait — pas l'ennemi qui t'imposait son tempo ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_ultime_tank", "Avant d'utiliser ton ultime, tu vérifiiais que tes alliés étaient en position pour convertir ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_reset", "Quand un fight était perdu (trop de désavantage), tu savais reculer avant de perdre ta vie ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_suivi_equipe", "Tes alliés DPS pouvaient suivre tes engages — tu n'allais pas trop loin trop vite ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "DPS": [
        ("role_cible", "Tu cherchais activement les supports ennemis plutôt que de tirer sur la première cible visible ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_positioning_dps", "Tu avançais de cover en cover — jamais exposé sans avoir un angle de retrait ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_ultime_dps", "Ton ultime a été utilisé sur des situations déjà favorables pour toi — pas en désespoir ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_suivi_tank", "La seconde où ton tank engageait, tu étais déjà en mouvement pour suivre ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_cooldowns_dps", "Tu gardais toujours au moins un cooldown défensif disponible en cas de contre-attaque ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_pression", "Tu maintenais une pression constante sur les supports ennemis, même sans les tuer ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "Support": [
        ("role_heal_priorite", "Tu healais selon la priorité correcte : tank en engage → DPS en danger → les autres ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_survie_support", "Tu ne mourais pas stupidement — tu gérais ta survie avant de te soucier de ton heal ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_ultime_support", "Ton ultime a contré une situation critique ou sécurisé un fight déjà gagné ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_positioning_support", "Tu étais assez loin pour survivre mais assez proche pour être utile — le bon équilibre ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_awareness_support", "Tu anticipais qui allait avoir besoin de soin AVANT que leur vie descende dans le rouge ?", ["Toujours", "Parfois", "Jamais"]),
        ("role_pression_support", "Tu profitais des moments calmes pour infliger des dégâts/harceler les ennemis ?", ["Toujours", "Parfois", "Jamais"]),
    ],
}

QUESTIONS_PAR_SPECIALISATION = {
    "tank_dive": [
        ("spec_cible_dive", "Tes dives ciblaient les supports ou DPS isolés — jamais le tank qui attend ton engage ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_timing_dive", "Tu divais uniquement quand ton équipe était en position pour convertir le kill ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_sortie_dive", "Sur un dive raté (personne ne suit, tu es seul), tu sortais immédiatement sans forcer ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cooldowns_dive", "Tu conservais un cooldown de sortie AVANT d'engager — pas après avoir tout utilisé ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_isolation", "Tu isolais ta cible du reste de l'équipe ennemie avant de commiter ton engage ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "tank_defensif": [
        ("spec_bouclier", "Ton bouclier couvrait l'équipe entière — pas juste toi ou une direction inutile ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_angle_defensif", "Tu choisissais des angles qui forçaient l'ennemi à venir dans ton avantage ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_pression", "Tu avançais progressivement sur l'objectif sans jamais reculer sans raison valable ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_timing_charge", "Tes charges/engages décisifs étaient déclenchés quand l'ennemi était groupé ou distrait ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_gestion_bouclier", "Tu retirais ton bouclier avant qu'il soit détruit pour le recharger au bon moment ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "tank_brawl": [
        ("spec_resource_brawl", "Ta ressource principale (énergie Zarya, hook CD Roadhog...) était toujours gérée avec précision ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_fight_brawl", "Tu cherchais les espaces fermés et courtes distances — terrain où tu domines naturellement ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_dos_brawl", "Tu avais toujours un mur ou une sortie derrière toi — jamais pris en sandwich ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_combo_brawl", "Tes abilities s'enchaînaient dans le bon ordre pour maximiser les burst de dégâts ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cible_brawl", "Tu ciblais la cible la plus molle/isolée dans le groupe — pas forcément la plus proche ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "dps_hitscan": [
        ("spec_aim", "Ton aim était consistant du début à la fin — pas juste en début de session ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cover_hitscan", "Tu peekais depuis un cover, tirais, et retournais en cover — cycle propre et répété ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_angle_hitscan", "Tu cherchais des angles inattendus qui surprenaient l'ennemi plutôt que les angles évidents ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cible_hitscan", "Tu ignorais le tank pour chercher le support ou le DPS fragile derrière ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_distance_hitscan", "Tu maintenais la distance qui maximise ton efficacité selon ton héros ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "dps_flanker": [
        ("spec_timing_flanker", "Tu attendais que l'ennemi soit engagé sur ton équipe avant de flanker — jamais trop tôt ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_survie_flanker", "Sur un flanc raté, tu reculais immédiatement sans essayer de forcer l'élimination ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cible_flanker", "Le support ennemi était ta cible prioritaire — pas le DPS ou le tank qui peut se défendre ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_cooldowns_flanker", "Tu gardais ton escape (Blink, Swift Strike, Fade...) pour sortir — pas juste pour engage ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_reset_flanker", "Après un kill, tu te repositionnais avant de ré-engager plutôt que de continuer en mode berserk ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "dps_projectile": [
        ("spec_lead", "Tu anticipais le déplacement ennemi — tu tirais où ils ALLAIENT être, pas où ils étaient ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_zone_projectile", "Tes abilities créaient des zones de danger que l'ennemi devait éviter ou traverser ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_distance_projectile", "Tu jouais à la distance optimale de ton héros — ni trop loin ni trop proche ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_combo_projectile", "Tes abilities s'enchaînaient pour burst une cible avant qu'elle puisse réagir ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_splash_projectile", "Tu profitais des dégâts de zone pour harceler plusieurs ennemis groupés simultanément ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "support_heal": [
        ("spec_heal_continu", "Tu maintenais un heal continu sans jamais laisser une vie descendre en dessous de 50% sans raison ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_ressource_heal", "Tu anticipais les pics de dégâts pour ne jamais être à court de ressource au mauvais moment ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_boost", "Tes boosts/nanos étaient utilisés sur les moments décisifs — engage tank, ultime DPS clé ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_antiheal", "Tu utilisais l'anti-heal sur les supports ennemis plutôt que de spam heal tes alliés ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_sleep_grenade", "Tes outils de contrôle (sleep, grenade, immortality field...) sauvaient des fights critiques ?", ["Toujours", "Parfois", "Jamais"]),
    ],
    "support_utilitaire": [
        ("spec_utilite", "Ton aura/buff principal était actif en permanence sur les bonnes cibles ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_peel_utilitaire", "Tu survivais seul face aux flankers sans avoir besoin que ton équipe te sauve ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_positioning_utilitaire", "Ta position maximisait l'impact de tes abilities sur le maximum d'alliés simultanément ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_aggression_utilitaire", "Tu profitais des moments sûrs pour harceler et infliger des dégâts significatifs ?", ["Toujours", "Parfois", "Jamais"]),
        ("spec_discord_speed", "Tu switchais entre tes modes (speed/heal pour Lucio, discord/harmony pour Zenyatta...) intelligemment ?", ["Toujours", "Parfois", "Jamais"]),
    ],
}

QUESTION_RESULTAT = ("resultat", "Résultat global de la session ?", ["Victoire majoritaire", "Partagé", "Défaite majoritaire"])

# ==================== DIAGNOSTICS NIVEAU COACH ====================

DIAGNOSTICS_COMMUNS = {
    "comm_objectif": ("Jamais", "Ton instinct de kill te coûte des rounds entiers. En Overwatch, l'objectif n'est pas une suggestion — c'est la seule chose qui compte sur le scoreboard final. La prochaine fois qu'une opportunité de kill te détourne de l'objectif, demande-toi : est-ce que ce kill me donne l'objectif ou est-ce que je sacrifie l'objectif pour ce kill ?"),
    "comm_rotation": ("Jamais", "Tu réagis au lieu d'anticiper — c'est la différence entre un joueur moyen et un bon joueur. Les rotations adverses sont prévisibles si tu analyses la map. Pose-toi cette question avant chaque fight : d'où peut arriver l'ennemi dans 10 secondes ? Prends position là-bas avant qu'il y arrive."),
    "comm_minimap": ("Jamais", "La mini-map est ton radar. Un ennemi invisible n'est pas un ennemi absent — il est quelque part sur la map en train de te flanker. Force-toi à regarder la mini-map après chaque kill ou mort, même 0.5 seconde. Avec le temps ça devient automatique."),
    "comm_flankers": ("Jamais", "Te faire surprendre par un flanker c'est un manque d'awareness, pas de malchance. Avant chaque teamfight, demande-toi : où est la Tracer ? Où est le Genji ? Si tu ne les vois pas devant, ils arrivent par derrière. Anticipe."),
    "comm_tilt": ("Jamais", "Le tilt est l'ennemi numéro un de ta progression. Chaque mort sous énervement génère deux autres erreurs. La technique la plus efficace : après une mort frustrante, prends 2 secondes sur le temps de respawn pour te focaliser uniquement sur la prochaine décision — pas sur ce qui vient de se passer."),
    "comm_communication": ("Jamais", "Le silence en jeu d'équipe est une faute tactique. Tu n'as pas besoin de faire des callouts parfaits — trois phrases suffisent pour changer un fight : 'Ultime prêt', 'Je dive', 'Repli'. Ces informations valent plus que dix bons tirs."),
    "comm_ultime_tracking": ("Jamais", "Ne pas tracker les ultimes adverses c'est jouer à l'aveugle. Grave dans ta mémoire les durées des ultimes clés : Graviton Surge, Sound Barrier, Transcendance, Nano Boost. Si tu ne les as pas vus depuis 2 minutes, ils sont prêts. Joue en conséquence."),
}

DIAGNOSTICS_PAR_ROLE = {
    "Tank": {
        "role_espace": ("Jamais", "Tu occupes de l'espace mais tu ne crées pas d'espace — ce n'est pas la même chose. Créer de l'espace c'est forcer les ennemis à te deal plutôt que de frapper tes alliés. Si tes DPS meurent sans avoir pu tirer, c'est que tu n'as pas suffisamment occupé l'attention adverse. Engage plus agressivement pour que les ennemis n'aient d'yeux que pour toi."),
        "role_peel": ("Jamais", "Un support mort coûte le fight entier — même le meilleur engage du monde ne sert à rien sans heal. Quand tu entends ton Ana crier ou que tu vois une Tracer en train de le harceler, tu abandonnes ton engage et tu reviens. Ce n'est pas reculer, c'est jouer intelligemment."),
        "role_tempo": ("Jamais", "Tu subis le tempo de l'adversaire au lieu de l'imposer. Le tank définit QUAND le fight se passe. Si tu attends que l'ennemi engage sur toi, tu es déjà en retard. Choisis le moment, le terrain, l'angle — et engage en premier depuis une position favorable."),
        "role_ultime_tank": ("Jamais", "Ton ultime utilisé seul vaut 30% de son potentiel. Un Primal Rage sans que tes DPS soient prêts à convertir, c'est du gaspillage. Annonce 'ultime dans 5 secondes' pour que ton équipe se positionne. L'ultime coordonné change le match, l'ultime solo change une vie."),
        "role_reset": ("Jamais", "Mourir en refusant de reculer n'est pas du courage — c'est offrir un avantage gratuit à l'ennemi. Savoir quand reset un fight perdu est la compétence la plus sous-estimée du Tank. Si tu perds 2 alliés ou si ton heal est mort, recule immédiatement et regroup. Un fight raté reset vaut mieux qu'un fight perdu avec 5 morts."),
        "role_suivi_equipe": ("Jamais", "Tes engages partent trop vite ou trop loin — tes alliés n'arrivent pas à suivre. Regarde derrière toi avant d'engager. Si ton Lucio n'est pas à portée ou si ton DPS est encore en retrait, ralentis. Un engage sans follow-up c'est un 1v5 non assumé."),
    },
    "DPS": {
        "role_cible": ("Jamais", "Tu tires sur ce qui bouge plutôt que sur ce qui compte. La hiérarchie des cibles en Overwatch est absolue : Support ennemi → DPS fragile → Tank. Le tank est la dernière priorité — il est fait pour absorber. Cherche activement l'Ana ou le Zenyatta derrière, même si c'est moins accessible."),
        "role_positioning_dps": ("Jamais", "Tu te retrouves régulièrement exposé sans couverture — c'est ce qui te tue. Le DPS joue un jeu de peek : tu sors, tu tires, tu rentres. Jamais statique, jamais à découvert plus de 2 secondes. Si tu n'as pas de cover à moins de 3 pas, reposition-toi avant d'engager."),
        "role_ultime_dps": ("Jamais", "Tu utilises ton ultime pour te sortir de situations difficiles plutôt que pour convertir des situations favorables. L'ultime DPS doit amplifier un avantage déjà existant — pas créer un avantage depuis zéro. Attends que ton tank ait engagé, que les ennemis soient regroupés, et que tu sois en position."),
        "role_suivi_tank": ("Jamais", "Ton tank engage dans le vide parce que tu arrives 2 secondes trop tard. Cette fenêtre de 2 secondes c'est la différence entre convertir le kill et voir ton tank mourir seul. Quand tu vois ton tank bouger vers l'avant, tu y vas immédiatement — pas après avoir finit ton reload."),
        "role_cooldowns_dps": ("Jamais", "Tu gaspilles tes cooldowns défensifs en phase offensive et tu te retrouves nu quand l'ennemi contre-attaque. La règle : garde toujours UN cooldown défensif en réserve. Dash, Fade, Combat Roll — un de ces outils doit être disponible à tout moment pour ta survie."),
        "role_pression": ("Jamais", "Tu n'existes pas dans le fight si tu ne touches pas les supports ennemis. Même sans les tuer, les forcer à se repositionner ou à utiliser leurs cooldowns c'est de la pression utile. Un Ana qui esquive tes tirs ne soigne pas son tank — c'est déjà un avantage pour toi."),
    },
    "Support": {
        "role_heal_priorite": ("Jamais", "Tu heales en mode panique — le premier allié que tu vois plutôt que le plus important. Établis une hiérarchie mentale avant chaque fight : qui a le plus besoin de vivre ? Généralement c'est ton tank en engage, puis le DPS le plus exposé. Les autres attendent."),
        "role_survie_support": ("Jamais", "Tu traites ta propre survie comme secondaire — c'est l'erreur classique du support débutant. Un support mort heal 0 HP par seconde. Ta mort est la pire chose qui puisse arriver à ton équipe. Avant de sauver un allié à 10% de vie, assure-toi que tu ne vas pas mourir en essayant."),
        "role_ultime_support": ("Jamais", "Ton ultime arrive trop tard ou sur des situations déjà perdues. L'ultime support a deux usages optimaux : contrer un ultime adverse dévastateur (Sound Barrier contre Death Blossom) ou sécuriser un fight déjà à ton avantage. Évite de l'utiliser en réaction — anticipe."),
        "role_positioning_support": ("Jamais", "Tu es trop proche de l'action — c'est pour ça que tu meurs. Le support doit rester à la distance maximale depuis laquelle il peut encore être utile. Sur chaque map, identifie une position légèrement en retrait, couverte sur au moins deux angles, d'où tu vois tes alliés sans être en première ligne."),
        "role_awareness_support": ("Jamais", "Tu réagis aux dégâts au lieu d'anticiper les besoins. Regarde constamment les barres de vie — pas seulement quand quelqu'un crie. Si tu vois ton tank s'engager sans que son heal soit ready, tu prépares le heal AVANT qu'il prenne des dégâts. L'anticipation est ce qui sépare un bon support d'un excellent."),
        "role_pression_support": ("Jamais", "Tu joues support passif à 100% du temps — mais les moments calmes sont des opportunités. Quand personne ne prend de dégâts, tes balles/orbes/soins ne doivent pas être gaspillés. Harcèle les ennemis, force-les à reculer, crée de la pression. Un support qui ne fait rien entre les fights laisse de l'impact sur la table."),
    },
}

DIAGNOSTICS_PAR_SPECIALISATION = {
    "tank_dive": {
        "spec_cible_dive": ("Jamais", "Tu dives sur le tank adverse — c'est la pire cible possible pour un dive tank. Le tank est fait pour survivre aux engages. Tes dives doivent systématiquement viser les supports : l'Ana qui est seule derrière, le Zenyatta sans protection, le Baptiste qui a utilisé son Immortality Field. Isole-les du groupe avant d'engager."),
        "spec_timing_dive": ("Jamais", "Tu dives en solo — c'est pour ça que ça ne convertit pas. Un dive tank sans follow-up DPS c'est un suicide assisté. Avant de sauter, vérifie visuellement que tes DPS sont en position et prêts à suivre. Si ton Tracer ou ton Genji est encore derrière, tu attends."),
        "spec_sortie_dive": ("Jamais", "Tu forces des dives ratés jusqu'à ta mort au lieu de sortir proprement. Dès que tu réalises que personne ne suit, que ta cible a des cooldowns disponibles, ou que tu prends des dégâts des deux côtés — tu sors IMMÉDIATEMENT. Un dive raté proprement sorti te permet de retenter dans 10 secondes."),
        "spec_cooldowns_dive": ("Jamais", "Tu utilises tous tes cooldowns de mobilité pour entrer et tu n'as plus rien pour sortir. C'est l'erreur la plus commune sur les tank dive. Garde TOUJOURS un cooldown de sortie : une charge Winston, un Boost D.Va, un Rocket Punch Doomfist. Sans escape tu es une cible statique."),
        "spec_isolation": ("Jamais", "Tu dives dans le groupe ennemi entier au lieu d'isoler une cible. Un bon dive c'est couper une cible du reste — la mettre dans une position où personne ne peut la sauver. Utilise les obstacles, les angles, la verticalité pour séparer ta proie du groupe avant de commiter."),
    },
    "tank_defensif": {
        "spec_bouclier": ("Jamais", "Ton bouclier te protège toi mais pas ton équipe — ce n'est pas son rôle. Un bouclier bien positionné doit créer un couloir sûr pour tes alliés de progresser. Pense à qui a besoin d'être couvert : ton Ana qui heale depuis derrière, ton DPS qui doit avancer. Place le bouclier pour eux, pas pour toi."),
        "spec_angle_defensif": ("Jamais", "Tu avances en ligne droite — l'ennemi te voit venir depuis 20 mètres. Les meilleurs Reinhardt et Sigma utilisent la géographie de la map pour créer des angles qui minimisent leur exposition. Approche depuis un côté, force l'ennemi à pivoter, engage quand il est hors de position."),
        "spec_pression": ("Jamais", "Tu recules trop facilement — l'ennemi prend l'objectif pendant que tu 'joues safe'. Jouer défensif ne signifie pas reculer à la moindre pression. Tiens ta position sur l'objectif, oblige l'ennemi à venir à toi sur ton terrain. Chaque pas en arrière est un cadeau."),
        "spec_timing_charge": ("Jamais", "Tes charges partent au mauvais moment — soit trop tôt sur une cible prête, soit trop tard sur une cible qui a récupéré. La fenêtre idéale : ennemi qui vient d'utiliser son escape, ennemi qui reload, ennemi qui est dos à un mur. Attends ce moment précis."),
        "spec_gestion_bouclier": ("Jamais", "Ton bouclier est détruit trop souvent parce que tu le laisses en place jusqu'au bout. Retire ton bouclier avant qu'il soit brisé pour commencer sa recharge — un bouclier brisé te laisse vulnérable 5 secondes. Apprends à sentir quand le retirer et le replacer."),
    },
    "tank_brawl": {
        "spec_resource_brawl": ("Jamais", "Ta ressource principale est gaspillée sur des situations non optimales. L'énergie de Zarya se gagne sur des alliés en danger — pas sur toi-même par précaution. Le hook de Roadhog doit toucher une cible isolée, jamais le tank. Traite ta ressource comme ta capacité ultime : utilise-la uniquement quand ça compte vraiment."),
        "spec_fight_brawl": ("Jamais", "Tu prends des fights en espace ouvert où tu perds naturellement. Les tanks brawl dominent dans les couloirs, les coins, les espaces fermés où la longue portée adverse ne peut pas s'exprimer. Cherche activement ces terrains — déplace le fight vers un endroit favorable plutôt que de te battre où l'ennemi veut."),
        "spec_dos_brawl": ("Jamais", "Tu te retrouves régulièrement pris en sandwich — ce qui annule ton avantage naturel en brawl. Toujours avoir un mur ou une sortie dans ton dos. Avant d'engager, vérifie ton 6 heures. Un tank brawl pris à revers est un tank mort."),
        "spec_combo_brawl": ("Jamais", "Tes abilities partent dans le désordre et tu perds du burst damage. L'ordre optimal varie selon le héros mais le principe est universel : tu immobilises/ralentis d'abord, puis tu burst. Roadhog : Hook → Breaker → Pigpen → Tir. Zarya : Particule sur allié en danger → énergie → burst. Répète ces séquences jusqu'à ce qu'elles deviennent automatiques."),
        "spec_cible_brawl": ("Jamais", "Tu tapes dans le tas au lieu de cibler intelligemment. Même en brawl il y a une cible prioritaire : le support le plus accessible, le DPS le plus fragile, le tank le plus entamé. Identifie qui peut mourir le plus vite et focus-toi exclusivement sur cette cible."),
    },
    "dps_hitscan": {
        "spec_aim": ("Jamais", "Ton aim se dégrade au fil de la session — tu commences bien mais tu déclines après 30-45 minutes. C'est de la fatigue mentale. Solution : fais 10 minutes d'échauffement sur les serveurs d'entraînement AVANT ta session ranked. Et si tu sens ton aim baisser, prends 5 minutes de pause — continuer en déficit d'aim empire la situation."),
        "spec_cover_hitscan": ("Jamais", "Tu restes exposé trop longtemps après avoir tiré — l'ennemi a le temps de riposter. Le cycle optimal du hitscan : peek → 1-2 tirs précis → retour en cover → repositionnement → nouveau peek depuis un angle différent. Ce dernier point est crucial : ne peeke jamais deux fois du même angle contre un bon joueur."),
        "spec_angle_hitscan": ("Jamais", "Tu utilises les angles évidents que l'ennemi anticipe déjà. Les meilleurs joueurs hitscan cherchent en permanence des angles qui n'existent pas encore — hauteur, flanc, angle croisé. Un Sojourn sur un toit inattendu vaut trois fois plus qu'un Sojourn au niveau du sol."),
        "spec_cible_hitscan": ("Jamais", "Tu tires sur le tank parce que c'est la cible la plus grosse et la plus visible. C'est de la balle gaspillée. Cherche le support derrière — même partiellement visible, même à distance. Un rail gun Sojourn sur une Ana qui soigne vaut infiniment plus qu'un clip entier dans le bouclier de Reinhardt."),
        "spec_distance_hitscan": ("Jamais", "Tu joues à la mauvaise distance pour ton héros. Chaque hitscan a une plage optimale : Widowmaker veut la longue distance maximale, Sojourn veut le mid-range pour charger son rail, Cassidy veut le mid-close. Si tu te retrouves trop proche ou trop loin, repositionne-toi avant d'engager."),
    },
    "dps_flanker": {
        "spec_timing_flanker": ("Jamais", "Tu flankes trop tôt — l'ennemi n'est pas encore engagé sur ton équipe et il a toute l'attention disponible pour te deal. Le timing parfait : tu commences ton flanc PENDANT que ton tank engage en frontal. Les ennemis sont divisés entre deux menaces et ta cible n'a plus de soutien immédiat."),
        "spec_survie_flanker": ("Jamais", "Tu forces des situations perdues en flanc parce que tu veux 'finir le kill'. Sur un flanc raté, ta priorité absolue est de sortir vivant — pas d'éliminer la cible. Un flanker qui sort proprement peut retenter dans 5 secondes. Un flanker mort offre un avantage à l'ennemi pendant 15 secondes."),
        "spec_cible_flanker": ("Jamais", "Tu flankes le tank ou le DPS — des cibles qui peuvent se défendre seules ou qui ont des cooldowns défensifs. Le support ennemi est ta seule cible valable en flanc. Un Ana éliminé en flanc laisse le tank ennemi sans heal pour les 15 prochaines secondes — c'est un fight entier qui bascule."),
        "spec_cooldowns_flanker": ("Jamais", "Tu utilises TOUS tes cooldowns pour engager et tu n'as plus rien pour sortir quand ça tourne mal. La règle absolue du flanker : garde ton escape jusqu'à en avoir besoin pour fuir, pas pour engage. Tracer garde un Blink pour sortir. Genji garde son Swift Strike pour reset ou fuir. Sans escape tu es une cible facile."),
        "spec_reset_flanker": ("Jamais", "Après un kill tu continues en mode berserk et tu meurs sur la cible suivante. Le reset est fondamental : après chaque élimination, sors de la ligne de vue, reprends ta vie si possible, analyse la situation, et entre dans le prochain engage frais. Le flanker qui ne reset pas meurt dans les 10 secondes qui suivent son premier kill."),
    },
    "dps_projectile": {
        "spec_lead": ("Jamais", "Tu vises où la cible EST au lieu de viser où elle VA. Le aim lead s'apprend par la pratique : plus la cible est loin et rapide, plus tu dois anticiper. Commence par t'entraîner sur des cibles qui courent en ligne droite, puis sur des cibles qui strafent. Avec le temps l'anticipation devient instinctive."),
        "spec_zone_projectile": ("Jamais", "Tu utilises tes abilities pour faire des dégâts directs alors qu'elles brillent en contrôle de zone. Un Tire de Junkrat placé à l'entrée d'un couloir force l'ennemi à le contourner — même sans le toucher. Utilise tes projectiles pour créer des zones que l'ennemi doit éviter, pas juste pour infliger des dégâts."),
        "spec_distance_projectile": ("Jamais", "Tu te retrouves régulièrement à la mauvaise distance pour ton héros. Pharah veut la hauteur et la longue portée. Hanzo veut le mid-range avec couverts. Junkrat veut les espaces fermés et corridors. Si tu joues Pharah au niveau du sol ou Junkrat à longue portée, tu t'handicapes toi-même."),
        "spec_combo_projectile": ("Jamais", "Tes abilities partent dans le désordre et ta cible a le temps de réagir entre chaque. Le burst combo du projectile DPS doit être assez rapide pour ne pas laisser de fenêtre de réponse. Hanzo : Sonic Arrow → Storm Arrow sur cible révélée. Mei : Icicle charge → Blizzard. Pratique ces séquences jusqu'à ce qu'elles partent automatiquement."),
        "spec_splash_projectile": ("Jamais", "Tu vises les cibles individuelles alors que tes projectiles ont de la zone. Sur un groupe ennemi compact, vise entre les cibles plutôt qu'une seule — le splash touche tout le monde. Junkrat, Pharah, Hanzo infligent des dégâts exponentiels sur des ennemis groupés si tu exploites correctement leur zone d'effet."),
    },
    "support_heal": {
        "spec_heal_continu": ("Jamais", "Tu laisses des alliés descendre trop bas avant de réagir — et à ce niveau là, le heal ne suffit plus. La règle des 70% : dès qu'un allié passe sous 70% de vie, tu commences à le healer. Pas à 30%, pas en urgence — à 70%. À ce niveau tu as encore le temps de le remonter proprement sans paniquer."),
        "spec_ressource_heal": ("Jamais", "Tu tombes à court de ressource au pire moment parce que tu heales de façon réactive. Anticipe les phases de fort dégâts : quand ton tank engage, quand une teamfight commence. Conserve de la ressource AVANT ces moments, pas pendant. Un Ana qui a gardé une grenade de heal pour le teamfight change le résultat du fight."),
        "spec_boost": ("Jamais", "Tes nanos/boosts partent sur des situations déjà gagnées ou en désespoir total. La fenêtre idéale : ton tank est sur le point d'engager un fight décisif, ou ton DPS a son ultime prêt et attend le bon moment. Annonce 'nano/boost disponible' pour que l'allié le plus impactant puisse demander."),
        "spec_antiheal": ("Jamais", "Tu utilises tes ressources pour heal au lieu de les utiliser pour empêcher l'ennemi de heal. Contre une équipe avec Mercy ou Ana, ta grenade d'anti-heal sur le groupe ennemi vaut plus que trois grenades de heal sur tes alliés. Si l'ennemi ne peut pas se soigner, tous tes alliés font plus de dégâts efficaces."),
        "spec_sleep_grenade": ("Jamais", "Tu n'utilises pas tes outils de contrôle au bon moment — ils sont sous-utilisés ou mal timés. Le Sleep Dart d'Ana n'est pas juste un outil de survie — c'est un annulateur d'ultime. Garde-le pour les moments critiques : ennemi qui utilise Death Blossom, Gravitic Flux, ou Dragonblade. Ce dart peut sauver un fight entier."),
    },
    "support_utilitaire": {
        "spec_utilite": ("Jamais", "Ton aura/buff principal n'est pas sur la bonne cible ou pas actif au bon moment. Lucio doit switcher speed/heal selon le moment — speed pour les approches et engages, heal pendant les combats. Zenyatta doit avoir Harmony sur la cible qui prend le plus de dégâts et Discord sur la cible prioritaire ennemie. Ce ne sont pas des buffs passifs — ce sont des décisions actives constantes."),
        "spec_peel_utilitaire": ("Jamais", "Tu dépends de ton équipe pour te sauver quand un flanker t'attaque. Un support utilitaire doit être capable de se défendre seul le temps que de l'aide arrive. Zenyatta : orbe de discord + tirs focus. Lucio : boop + murs pour fuir. Kiriko : téléport hors de danger. Ces outils de survie doivent être réflexes."),
        "spec_positioning_utilitaire": ("Jamais", "Ta position ne maximise pas l'impact de tes abilities. Lucio sur un mur surélevé peut booper plusieurs ennemis en même temps. Zenyatta derrière un cover partiel peut maintenir son Discord sans s'exposer. Ana sur une hauteur a un angle de tir sur toute la map. Chaque map a des positions 'broken' pour ton héros — trouve-les et utilise-les."),
        "spec_aggression_utilitaire": ("Jamais", "Tu joues trop passif entre les phases de combat — tu attends au lieu d'agir. Entre deux engages, tu dois harceler l'ennemi : Zenyatta inflige des dégâts significatifs à longue portée, Lucio peut booper des ennemis hors de position, Kiriko peut se téléporter pour pressure un flanc. Un support utilitaire actif contrôle le tempo du match."),
        "spec_discord_speed": ("Jamais", "Tu maintiens le même mode/aura toute la game au lieu de switcher selon la situation. Lucio en heal permanent manque la moitié de son impact — le speed boost sur une équipe qui engage peut décider du fight. Zenyatta avec harmony sur le mauvais allié perd de l'efficacité. Lis la situation et adapte en temps réel."),
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
        diagnostics.append(("✅", f"Session propre sur {hero}. Aucun problème majeur détecté — continue dans cette direction."))

    return diagnostics

def get_profil(pseudo):
    return profils_col.find_one({"pseudo": pseudo})

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
        stats_heroes[h]["winrate"] = round((stats_heroes[h]["victoires"] / stats_heroes[h]["total"]) * 100)
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
        {"date": date, "winrate": round((v["victoires"] / v["total"]) * 100), "sessions": v["total"]}
        for date, v in sorted(sessions_par_date.items())
    ]
    return {
        "total": total, "victoires": victoires, "winrate": winrate,
        "stats_heroes": stats_heroes, "top_erreurs": top_erreurs, "progression": progression,
    }

# ==================== ROUTES ====================

@app.route("/")
def index():
    profils = list(profils_col.find({}, {"pseudo": 1, "date_creation": 1, "sessions": 1}))
    profils_liste = [
        {"pseudo": p["pseudo"], "sessions": len(p.get("sessions", [])), "date_creation": p.get("date_creation", "")}
        for p in profils
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
            if action == "creer":
                if profils_col.find_one({"pseudo": pseudo}):
                    erreur = "Ce pseudo est déjà pris."
                else:
                    profils_col.insert_one({
                        "pseudo": pseudo,
                        "password": hash_password(password),
                        "date_creation": datetime.now().strftime("%Y-%m-%d"),
                        "sessions": []
                    })
                    session["pseudo"] = pseudo
                    return redirect(url_for("dashboard"))
            elif action == "connexion":
                profil = profils_col.find_one({"pseudo": pseudo})
                if not profil:
                    erreur = "Profil introuvable."
                elif profil["password"] != hash_password(password):
                    erreur = "Mot de passe incorrect."
                else:
                    session["pseudo"] = pseudo
                    return redirect(url_for("dashboard"))
    return render_template("login.html", erreur=erreur)

@app.route("/dashboard")
def dashboard():
    if "pseudo" not in session:
        return redirect(url_for("index"))
    profil = get_profil(session["pseudo"])
    if not profil:
        return redirect(url_for("index"))
    sessions = profil.get("sessions", [])
    stats = calculer_stats_profil(sessions)
    return render_template("dashboard.html", pseudo=session["pseudo"], stats=stats, nb_sessions=len(sessions))

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
        "Tank": {"Dive": HEROES_PAR_SPECIALISATION["tank_dive"], "Défensif": HEROES_PAR_SPECIALISATION["tank_defensif"], "Brawl": HEROES_PAR_SPECIALISATION["tank_brawl"]},
        "DPS": {"Hitscan": HEROES_PAR_SPECIALISATION["dps_hitscan"], "Flanker": HEROES_PAR_SPECIALISATION["dps_flanker"], "Projectile": HEROES_PAR_SPECIALISATION["dps_projectile"]},
        "Support": {"Heal Principal": HEROES_PAR_SPECIALISATION["support_heal"], "Utilitaire": HEROES_PAR_SPECIALISATION["support_utilitaire"]},
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
    return render_template("questions_communes.html", questions=QUESTIONS_COMMUNES, question_resultat=QUESTION_RESULTAT, heroes=session.get("heroes_joues", []))

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
    return render_template("questions_hero.html", hero=hero, role=role,
                           spec=spec.replace("_", " ").title() if spec else "",
                           questions=questions_hero_list, index=index + 1, total=len(heroes_joues))

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
        "date": date, "mode": mode, "heroes": heroes_joues,
        "resultat": resultat, "reponses_communes": reponses_communes,
        "reponses_par_hero": reponses_par_hero, "diagnostics": diagnostics_par_hero
    }
    profils_col.update_one({"pseudo": pseudo}, {"$push": {"sessions": nouvelle_session}})
    return render_template("diagnostic.html", heroes=heroes_joues, diagnostics_par_hero=diagnostics_par_hero,
                           resultat=resultat, mode=mode, date=date, pseudo=pseudo)

@app.route("/progression")
def progression():
    if "pseudo" not in session:
        return redirect(url_for("index"))
    profil = get_profil(session["pseudo"])
    if not profil:
        return redirect(url_for("index"))
    sessions = profil.get("sessions", [])
    stats = calculer_stats_profil(sessions)
    return render_template("progression.html", pseudo=session["pseudo"], stats=stats)

if __name__ == "__main__":
    app.run(debug=True)
