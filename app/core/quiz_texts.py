"""Text- und Phasenkonstanten für Quiz-UI."""

PHASE_NAME = "name"
PHASE_GROUP = "group"
PHASE_NEIGHBORS = "neighbors"
PHASE_DONE = "done"

ROUND_REACTION = {
    "excellent": [
        "Runde sitzt. Nervig souverän.",
        "Volle Punktzahl. Wie unpraktisch für meine Häme.",
        "Perfekt getroffen. CSV weint still vor Respekt.",
    ],
    "good": [
        "Gute Runde. Nicht peinlich, das hilft.",
        "Solide. Das war fast geplant.",
        "Mehr richtig als falsch, seltene Feiertagsstimmung.",
    ],
    "mid": [
        "Gemischte Runde. Der Mittelwert lebt.",
        "Halb Treffer, halb Abenteuerurlaub.",
        "Okay-ish. Das war statistisch legal.",
    ],
    "bad": [
        "Runde war sportlich… für die Fehlersammlung.",
        "Mutig geraten, Fakten eher dekorativ.",
        "Trefferlage: kreativ verteilt.",
    ],
}

HISTORY_REACTION = {
    "elite": [
        "Historisch bist du unangenehm stark.",
        "Gesamtquote ist frech gut.",
    ],
    "stable": [
        "Gesamt solide, leider nachvollziehbar.",
        "Historie zeigt brauchbare Konstanz.",
    ],
    "shaky": [
        "Historie schwankt wie WLAN im Altbau.",
        "Quote mit Charakter, aber wenig Präzision.",
    ],
}

STREAK_REACTION = {
    "hot": [
        "Serie läuft, Ego im Aufwärmprogramm.",
        "Streak aktiv. Selbstbewusstsein bitte anschnallen.",
    ],
    "cold": [
        "Serie beendet. Bodenhaftung wiederhergestellt.",
        "Kein Lauf gerade, aber immerhin ehrlich.",
    ],
    "neutral": [
        "Serie unauffällig. Bureaucracy-Modus.",
        "Kein Hype, kein Absturz, nur Arbeit.",
    ],
}

VOLUME_REACTION = {
    "new": [
        "Noch frühe Datenlage, also nur sanfte Häme.",
        "Wenige Versuche. Urteil vertagt.",
    ],
    "experienced": [
        "Genug Versuche für belastbare Ironie.",
        "Datenbasis steht. Ausreden werden teurer.",
    ],
    "veteran": [
        "Sehr viele Versuche. Das ist inzwischen ein Handwerk.",
        "Langzeitprojekt läuft. Die Statistik kennt dich beim Vornamen.",
    ],
}

DIFFICULTY_REACTION = {
    "high": [
        "Algorithmus stuft die Person als Baustelle ein.",
        "System sagt: bitte öfter wiederholen.",
    ],
    "mid": [
        "Schwierigkeit mittel – keine Ausreden, keine Dramen.",
        "Aktuell normalgewichtet, also fair genug.",
    ],
    "low": [
        "System stuft das schon als ziemlich sicher ein.",
        "Niedrige Wiederholungspriorität. Fast langweilig.",
    ],
}

TIME_REACTION = {
    "very_fast": [
        "Antworttempo: Blitzmodus, kaum unheimlich.",
        "Sehr schnell geantwortet. Kaffee war wohl on point.",
    ],
    "fast": [
        "Tempo war flink genug für gute Ausreden.",
        "Zügig geantwortet, ohne kompletten Kontrollverlust.",
    ],
    "normal": [
        "Tempo lag im normalen Bereich.",
        "Antwortzeit war unspektakulär vernünftig.",
    ],
    "slow": [
        "Etwas länger gebraucht als der Schnitt.",
        "Tempo eher gemütlich, aber noch vertretbar.",
    ],
    "very_slow": [
        "Antwortzeit deutlich über Durchschnitt – epische Dramaturgie.",
        "Das war langsam genug für einen Director's Cut.",
    ],
}

DELTA_REACTION = {
    "well_above": [
        "Heute deutlich über Allgemeinstat.",
        "Spürbar besser als der Gruppenschnitt.",
    ],
    "above": [
        "Leicht über Allgemeinstat, sauber.",
        "Knapp besser als der Schnitt der Lerngruppe.",
    ],
    "near": [
        "Nahe am Allgemeinstat – solide Standardware.",
        "Fast deckungsgleich mit dem Gruppenniveau.",
    ],
    "below": [
        "Etwas unter Allgemeinstat, aber reparierbar.",
        "Knapp unter Gruppenschnitt, kein Weltuntergang.",
    ],
    "well_below": [
        "Heute klar unter Allgemeinstat. Mutig trotzdem.",
        "Deutlich unter dem Gruppenniveau – Trainingsfutter.",
    ],
}
