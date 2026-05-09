"""NaviX traffic engine — congestion scoring, routing, analytics."""
import random, time, heapq
from collections import defaultdict
from data import SEGMENTS, ZONES, INCIDENTS

_SEG = {}
_WEATHER = 'clear'
WEATHER_MULT = {'clear':1.0,'rain':1.25,'heavy_rain':1.55,'fog':1.15}

def _init():
    if _SEG: return
    for s in SEGMENTS:
        _SEG[s[0]] = {'score': random.uniform(20, 65), 'updated': time.time()}

def _tick():
    _init()
    m = WEATHER_MULT.get(_WEATHER, 1.0)
    for sid, st in _SEG.items():
        st['score'] = max(0, min(100, max(0, min(100, st['score'] + random.uniform(-8,8))) * (m**0.3)))
        st['updated'] = time.time()

def _color(s): return 'green' if s<30 else 'yellow' if s<55 else 'orange' if s<75 else 'red'
def _label(s): return 'Clear' if s<30 else 'Moderate' if s<55 else 'Heavy' if s<75 else 'Gridlock'

def get_kpis():
    _tick()
    scores = [s['score'] for s in _SEG.values()]
    avg = sum(scores)/len(scores)
    return {
        'city_score': round(100-avg, 1),
        'avg_congestion': round(avg, 1),
        'segments_clear': sum(1 for s in scores if s<30),
        'segments_moderate': sum(1 for s in scores if 30<=s<75),
        'segments_jammed': sum(1 for s in scores if s>=75),
        'total_segments': len(SEGMENTS),
        'active_incidents': sum(1 for i in INCIDENTS if i['status']=='active'),
        'weather': _WEATHER,
        'time_saved_minutes': random.randint(8, 22),
    }

def get_predictions():
    _tick()
    items = []
    for seg in SEGMENTS:
        sid = seg[0]
        score = _SEG[sid]['score']
        delta = random.uniform(-10,25) if score<70 else random.uniform(-15,5)
        if delta > 5:
            items.append({'segment_id':sid,'from_zone':seg[1],'to_zone':seg[2],
                          'current_score':round(score,1),'predicted_score':round(min(100,score+delta),1),
                          'delta':round(delta,1),'eta_minutes':random.choice([5,10,15])})
    items.sort(key=lambda x: x['predicted_score'], reverse=True)
    return items[:5]

def get_segments():
    _tick()
    return [{'id':s[0],'from':s[1],'to':s[2],'length_km':s[3],'lanes':s[4],
             'score':round(_SEG[s[0]]['score'],1),
             'color':_color(_SEG[s[0]]['score']),
             'label':_label(_SEG[s[0]]['score'])} for s in SEGMENTS]

def get_incidents(): return INCIDENTS

def get_zone_scores():
    _tick()
    zs = defaultdict(list)
    for seg in SEGMENTS:
        score = _SEG[seg[0]]['score']
        zs[seg[1]].append(score); zs[seg[2]].append(score)
    return [{'zone':z,'avg_score':round(sum(v)/len(v),1)} for z,v in zs.items()]

def get_analytics():
    return {'projected_revenue_y1_cr':2.0,'projected_revenue_y2_cr':6.5,
            'projected_revenue_y3_cr':12.0,'projected_revenue_y4_cr':18.0,
            'projected_revenue_y5_cr':25.0,'investment_required_cr':5.0,
            'roi_5_year_pct':316,'breakeven_year':2,'cities_targeted':100,
            'commuter_minutes_saved_per_day':18,'fuel_saved_per_user_per_month_inr':480,
            'co2_reduced_kg_per_user_per_year':156}

def get_state():
    return {'kpis':get_kpis(),'predictions':get_predictions(),
            'incidents':get_incidents(),'zone_scores':get_zone_scores(),'time':time.time()}

def set_weather(w):
    global _WEATHER
    if w in WEATHER_MULT: _WEATHER = w

def calculate_route(origin, destination):
    _tick()
    if not origin or not destination or origin not in ZONES or destination not in ZONES:
        return {'ok':False,'error':'Invalid origin or destination'}
    if origin == destination:
        return {'ok':False,'error':'Origin and destination are the same'}

    def dijkstra(graph, src, dst):
        dist = {z: float('inf') for z in ZONES}
        dist[src] = 0
        prev = {}
        heap = [(0, src)]
        visited = set()
        while heap:
            d, node = heapq.heappop(heap)
            if node in visited: continue
            visited.add(node)
            if node == dst: break
            for nb, w, sid, length in graph[node]:
                if nb not in visited and d+w < dist[nb]:
                    dist[nb] = d+w
                    prev[nb] = (node, sid, length)
                    heapq.heappush(heap, (d+w, nb))
        if dist[dst] == float('inf'): return None
        path, segs, total = [], [], 0
        cur = dst
        while cur != src:
            pn, sid, length = prev[cur]
            path.append(cur); segs.append(sid); total += length; cur = pn
        path.append(src); path.reverse(); segs.reverse()
        avg = sum(_SEG[s]['score'] for s in segs)/len(segs) if segs else 0
        return {'path':path,'segments':segs,'total_length_km':round(total,1),
                'avg_congestion':round(avg,1),
                'eta_minutes':round((total/30)*60*(1+avg/100),1),
                'fuel_estimate_inr':round(total*8,0)}

    base = defaultdict(list)
    for seg in SEGMENTS:
        sid,fz,tz,length,_ = seg
        w = length*(1+_SEG[sid]['score']/50)
        base[fz].append((tz,w,sid,length)); base[tz].append((fz,w,sid,length))

    main = dijkstra(base, origin, destination)
    if not main: return {'ok':False,'error':'No route found'}

    alts = []
    used = set(main['segments'])
    for _ in range(2):
        ag = defaultdict(list)
        for seg in SEGMENTS:
            sid,fz,tz,length,_ = seg
            w = length*(1+_SEG[sid]['score']/50) * (4 if sid in used else 1)
            ag[fz].append((tz,w,sid,length)); ag[tz].append((fz,w,sid,length))
        alt = dijkstra(ag, origin, destination)
        if alt and alt['path'] != main['path'] and not any(alt['path']==a['path'] for a in alts):
            alts.append(alt); used.update(alt['segments'])

    return {'ok':True,'origin':origin,'destination':destination,**main,'alternatives':alts}
