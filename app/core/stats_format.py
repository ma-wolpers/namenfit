"""Formatierungsfunktionen für Personen- und Gruppenstatistiken."""


def ratio_text(correct, wrong):
    total = correct + wrong
    if total == 0:
        return "–"
    return f"{round((correct / total) * 100)}%"


def ratio_percent(correct, wrong):
    total = correct + wrong
    if total <= 0:
        return 0
    return round((correct / total) * 100)


def format_percent(ratio):
    return f"{round(ratio * 100)}%"


def stats_text_level1(stats):
    shown = stats.get("shown", 0)
    correct = stats.get("correct", 0)
    wrong = stats.get("wrong", 0)
    streak = stats.get("streak", 0)
    ratio = ratio_text(correct, wrong)
    return (
        f"Level 1 · gezeigt {shown} · richtig {correct} · falsch {wrong} "
        f"· Quote {ratio} · Serie {streak}"
    )


def stats_text_level2(stats):
    shown = stats.get("shown", 0)
    correct = stats.get("correct", 0)
    wrong = stats.get("wrong", 0)
    streak = stats.get("streak", 0)

    overall_ratio = ratio_text(correct, wrong)
    group_ratio = ratio_text(stats.get("group_correct", 0), stats.get("group_wrong", 0))
    behind_ratio = ratio_text(
        stats.get("behind_correct", 0), stats.get("behind_wrong", 0)
    )
    front_ratio = ratio_text(stats.get("front_correct", 0), stats.get("front_wrong", 0))
    opposite_ratio = ratio_text(
        stats.get("opposite_correct", 0), stats.get("opposite_wrong", 0)
    )
    name_correct = int(stats.get("name_correct", 0))
    name_wrong = int(stats.get("name_wrong", 0))
    show_name_ratio = (name_correct + name_wrong) > 0
    name_ratio_text = (
        f" · Name {ratio_text(name_correct, name_wrong)}" if show_name_ratio else ""
    )

    return (
        f"Level 2 · gezeigt {shown} · gesamt {overall_ratio} · TG {group_ratio} "
        f"· Dahinter {behind_ratio} · Davor {front_ratio} · Gegenüber {opposite_ratio}"
        f"{name_ratio_text} · Serie {streak}"
    )
