def parse_es_coords(lat_str, lon_str):
    def convert_to_decimal(degree, minute, second, direction):
        decimal = degree + minute / 60 + second / 3600
        if direction in ["S", "W"]:
            decimal = -decimal
        return decimal

    lat_deg = int(lat_str[1:4])
    lat_min = int(lat_str[5:7])
    lat_sec = float(lat_str[8:13])
    lat_dir = lat_str[0]

    lon_deg = int(lon_str[1:4])
    lon_min = int(lon_str[5:7])
    lon_sec = float(lon_str[8:13])
    lon_dir = lon_str[0]

    latitude = convert_to_decimal(lat_deg, lat_min, lat_sec, lat_dir)
    longitude = convert_to_decimal(lon_deg, lon_min, lon_sec, lon_dir)

    return latitude, longitude
