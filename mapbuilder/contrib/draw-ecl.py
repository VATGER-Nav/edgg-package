#!/usr/bin/env python3

from pygeodesy import ellipsoidalVincenty as ev

lat = 47.675668611
lon = 9.522710278
brg = 240.144

fap_lat = 47.742503667
fap_lon = 9.695697583

loc_lat = 47.665279167
loc_lon = 9.495923833

count = 18

perps = [4, 18]


def back_bearing(brg: float):
    if brg >= 180:
        return brg - 180

    return brg + 180


def perp_bearing(brg: float):
    brg = brg + 90

    if brg >= 360:
        return brg - 360

    return brg


def draw_ecl(
    lat: float,
    lon: float,
    count: int,
    brg: float,
    fap_lat: float,
    fap_lon: float,
    loc_lat: float,
    loc_lon: float,
    perps,
):
    point = ev.LatLon(lat, lon)
    ecl_bearing = back_bearing(brg)
    offset_brg = perp_bearing(ecl_bearing)

    points = [point]

    for _ in range(0, count):
        point = point.destination(distance=1852, bearing=ecl_bearing)
        points.append(point)

    for perp_id in perps:
        four_miles = points[perp_id]

        offset = four_miles.destination(distance=900, bearing=offset_brg)
        offset2 = offset.destination(distance=700, bearing=offset_brg)

        offset3 = four_miles.destination(distance=900, bearing=back_bearing(offset_brg))
        offset4 = offset3.destination(distance=700, bearing=back_bearing(offset_brg))

        # print(f"// At mile {perp_id}")
        print(f"{offset.lat} {offset.lon}")
        print(f"{offset2.lat} {offset2.lon}")
        print()

        print(f"{offset3.lat} {offset3.lon}")
        print(f"{offset4.lat} {offset4.lon}")
        print()

    localizer = ev.LatLon(loc_lat, loc_lon)
    loc1 = localizer.destination(distance=463, bearing=offset_brg)
    loc2 = localizer.destination(distance=-463, bearing=offset_brg)
    print(f"{loc1.lat} {loc1.lon}")
    print(f"{loc2.lat} {loc2.lon}")
    print()

    fap = ev.LatLon(fap_lat, fap_lon).destination(distance=1852, bearing=ecl_bearing)
    offset_brg = perp_bearing(ecl_bearing)
    offset = fap.destination(distance=900, bearing=offset_brg)
    offset2 = offset.destination(distance=700, bearing=offset_brg)

    offset3 = fap.destination(distance=900, bearing=back_bearing(offset_brg))
    offset4 = offset3.destination(distance=700, bearing=back_bearing(offset_brg))

    # print(f"// 1 mile behind FAF")
    print(f"{offset.lat} {offset.lon}")
    print(f"{offset2.lat} {offset2.lon}")
    print()

    print(f"{offset3.lat} {offset3.lon}")
    print(f"{offset4.lat} {offset4.lon}")
    print()

    for p in points:
        print(f"{p.lat} {p.lon}")


draw_ecl(lat, lon, count, brg, fap_lat, fap_lon, loc_lat, loc_lon, perps)
