"""Street geometry enrichment — uses ORS if key provided, else zone centroids."""
import json, urllib.request as _urllib

ZONE_COORDS = {
    'Indiranagar':[12.9784,77.6408],'Whitefield':[12.9698,77.7499],
    'Koramangala':[12.9352,77.6245],'HSR Layout':[12.9116,77.6389],
    'BTM Layout':[12.9165,77.6101],'Jayanagar':[12.9300,77.5833],
    'JP Nagar':[12.9063,77.5857],'Banashankari':[12.9255,77.5468],
    'Rajajinagar':[12.9905,77.5530],'Malleshwaram':[13.0035,77.5710],
    'Hebbal':[13.0353,77.5970],'Yeshwanthpur':[13.0207,77.5494],
    'Marathahalli':[12.9591,77.6974],'Bellandur':[12.9261,77.6740],
    'Sarjapur':[12.8617,77.7846],'Electronic City':[12.8452,77.6602],
    'Bommanahalli':[12.8981,77.6258],'Begur':[12.8716,77.6281],
    'Yelahanka':[13.1004,77.5963],'Hennur':[13.0434,77.6399],
    'Frazer Town':[12.9875,77.6178],'MG Road':[12.9756,77.6197],
    'Brigade Road':[12.9719,77.6089],'Cubbon Park':[12.9763,77.5929],
    'Vidhana Soudha':[12.9794,77.5913],'Cunningham Road':[12.9894,77.5974],
    'Domlur':[12.9609,77.6387],'CV Raman Nagar':[12.9848,77.6601],
    'Old Airport Rd':[12.9609,77.6540],'ITPL':[12.9856,77.7272],
    'KR Puram':[13.0070,77.6936],'Mahadevapura':[12.9978,77.7017],
    'Brookefield':[12.9706,77.7082],'Kadugodi':[12.9927,77.7614],
    'Hoodi':[12.9891,77.7162],'Ramamurthy Nagar':[13.0190,77.6616],
    'TC Palya':[13.0000,77.6800],
}

def enrich_route_with_street_geometry(route, ors_api_key=''):
    if not route or not route.get('ok'):
        return route
    path = route.get('path', [])
    fallback = [ZONE_COORDS[z] for z in path if z in ZONE_COORDS]
    if ors_api_key and len(path) >= 2:
        coords = [[ZONE_COORDS[z][1], ZONE_COORDS[z][0]] for z in path if z in ZONE_COORDS]
        if len(coords) >= 2:
            try:
                req = _urllib.Request(
                    'https://api.openrouteservice.org/v2/directions/driving-car/geojson',
                    data=json.dumps({'coordinates': coords}).encode(),
                    headers={'Authorization': ors_api_key, 'Content-Type': 'application/json'},
                    method='POST')
                with _urllib.urlopen(req, timeout=5) as r:
                    data = json.loads(r.read())
                ors_geom = data['features'][0]['geometry']['coordinates']
                route['geometry'] = [[p[1], p[0]] for p in ors_geom]
                route['geometry_source'] = 'ors'
                return route
            except Exception:
                pass
    route['geometry'] = fallback
    route['geometry_source'] = 'centroids'
    return route
