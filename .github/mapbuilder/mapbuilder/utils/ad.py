def render_runways(ad: dict, length: float = 1.5, exclude: list | None = None) -> str:
    if exclude is None:
        exclude = []
    lines = []

    for rwy_id, data in ad.items():
        if rwy_id in exclude:
            continue

        if data["brg1"] == 0 and data["brg2"] == 0:
            continue

        lines.append(str(data["center"].move_to(length / 2, data["brg2"]).line_to(length, data["brg1"])))

    return "\n".join(lines)


def render_cl(ad: dict) -> str:
    lines = []

    for _, data in ad.items():
        lines.append(str(data["thr1"].line_to_fix(data["thr2"])))

    return "\n".join(lines)
