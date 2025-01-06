def render_sid(waypoints: list, restrictions: dict) -> str:
    lines = []
    count = len(waypoints)
    lines.append(f"TEXT:{waypoints[-1]}:{waypoints[-1][0:2]}:10:10")
    for idx, wpt in enumerate(waypoints):
        if idx == count - 1:
            break

        lines.append(f"LINE:{wpt}:{waypoints[idx + 1]}")

    return "\n".join(lines)
