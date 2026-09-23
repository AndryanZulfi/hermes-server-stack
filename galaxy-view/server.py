import json
import os
import re
import time
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get('PORT', 8899))
# Base dir: use script directory or /app
BASE_DIR = os.environ.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.environ.get('SKILLS_DIR', '/opt/data/skills' if os.path.exists('/opt/data/skills') else '/skills')
ACTIVE_EVENT_FILE = os.path.join(BASE_DIR, 'active_skill.json')
USAGE_JSON = '/opt/data/skills/.usage.json'   # updated by bump_use on every skill load
DEACTIVATE_DELAY = 15   # seconds after last use before deactivating

# Active skills tracked by usage-watcher
_usage_active: dict = {}   # skill_name -> last_used_at string
_usage_lock = threading.Lock()

category_colors = {
    'software-development': '#38bdf8',  # Sky / Slate Blue
    'productivity': '#34d399',          # Emerald / Sage
    'creative': '#fbbf24',              # Warm Amber
    'autonomous-ai-agents': '#818cf8',  # Indigo Slate
    'research': '#a78bfa',              # Iris Slate
    'apple': '#94a3b8',                 # Cool Platinum
    'media': '#fb923c',                 # Terracotta
    'email': '#2dd4bf',                 # Muted Teal
    'devops': '#60a5fa',                # Technical Blue
    'note-taking': '#10b981',           # Jade
    'social-media': '#cbd5e1',          # Silver
    'web': '#0ea5e9',                   # Deep Sky
    'agency-orchestration': '#f59e0b',  # Amber Gold
    'agency-engineering': '#38bdf8',    # Sky Blue
    'agency-qa-security': '#f43f5e',    # Rose Crimson
    'agency-product-design': '#ec4899', # Magenta Pink
    'agency-growth': '#10b981',         # Emerald Green
    'agency-domain': '#a78bfa'          # Iris Slate
}

# Subscribed SSE clients
clients = []
clients_lock = threading.Lock()

def discover_subskills(skill_root, skill_name, cat, max_subs=8):
    """Auto-detect subskills/sub-modules underneath any skill directory."""
    subs = []
    seen = set()
    
    # 1. Knowledge modules (highest priority: domain frameworks)
    kdir = os.path.join(skill_root, 'knowledge')
    if os.path.isdir(kdir):
        for f in sorted(os.listdir(kdir)):
            if f.endswith('.md') and not f.startswith('.'):
                slug = f[:-3]
                title = slug.replace('-', ' ').title()
                desc = f'{skill_name} domain: {title}'
                try:
                    with open(os.path.join(kdir, f), 'r', encoding='utf-8', errors='ignore') as fp:
                        for line in fp:
                            line = line.strip()
                            if line.startswith('#'):
                                raw = line.lstrip('#').strip()
                                if raw and len(raw) <= 28 and '—' not in raw and '(' not in raw:
                                    title = raw
                                break
                except Exception:
                    pass
                subs.append({
                    'id': f'{skill_name}-{slug}',
                    'label': title,
                    'type': 'subskill',
                    'category': cat,
                    'parent': skill_name,
                    'desc': desc
                })
                seen.add(slug)
                if len(subs) >= max_subs:
                    return subs

    # 1b. Governance Protocols (e.g. Vibe protocols)
    pdir = os.path.join(skill_root, 'protocols')
    if os.path.isdir(pdir) and len(subs) < max_subs:
        for f in sorted(os.listdir(pdir)):
            if f.endswith('.md') and not f.startswith('.'):
                slug = f[:-3]
                if slug in seen: continue
                title = slug.replace('-', ' ').title()
                desc = f'{skill_name} protocol: {title}'
                try:
                    with open(os.path.join(pdir, f), 'r', encoding='utf-8', errors='ignore') as fp:
                        for line in fp:
                            line = line.strip()
                            if line.startswith('#'):
                                raw = line.lstrip('#').strip()
                                if raw and len(raw) <= 28 and '—' not in raw and '(' not in raw:
                                    title = raw
                                break
                except Exception:
                    pass
                subs.append({
                    'id': f'{skill_name}-{slug}',
                    'label': title,
                    'type': 'subskill',
                    'category': cat,
                    'parent': skill_name,
                    'desc': desc
                })
                seen.add(slug)
                if len(subs) >= max_subs:
                    return subs

    # 2. Reference guides & documentation
    rdir = os.path.join(skill_root, 'references')
    if os.path.isdir(rdir) and len(subs) < max_subs:
        for f in sorted(os.listdir(rdir)):
            if f.endswith('.md') and not f.startswith('.'):
                slug = f[:-3]
                if slug in seen: continue
                title = slug.replace('-', ' ').title()
                desc = f'{skill_name} reference: {title}'
                try:
                    with open(os.path.join(rdir, f), 'r', encoding='utf-8', errors='ignore') as fp:
                        for line in fp:
                            line = line.strip()
                            if line.startswith('#'):
                                raw = line.lstrip('#').strip()
                                if raw and len(raw) <= 28 and '—' not in raw and '(' not in raw:
                                    title = raw
                                break
                except Exception:
                    pass
                subs.append({
                    'id': f'{skill_name}-{slug}',
                    'label': title,
                    'type': 'subskill',
                    'category': cat,
                    'parent': skill_name,
                    'desc': desc
                })
                seen.add(slug)
                if len(subs) >= max_subs:
                    return subs

    # 3. Executable tool scripts / CLI clients
    sdir = os.path.join(skill_root, 'scripts')
    if os.path.isdir(sdir) and len(subs) < max_subs:
        for f in sorted(os.listdir(sdir)):
            if f.endswith(('.py', '.sh', '.js')) and not f.startswith(('_', '.')):
                raw_slug = f.rsplit('.', 1)[0]
                if raw_slug in seen or raw_slug in ('setup', 'test', '__init__', 'conftest'): continue
                slug = raw_slug.replace('_', '-')
                title = raw_slug.replace('_', ' ').replace('-', ' ').title()
                subs.append({
                    'id': f'{skill_name}-{slug}',
                    'label': title,
                    'type': 'subskill',
                    'category': cat,
                    'parent': skill_name,
                    'desc': f'{skill_name} tool script: {f}'
                })
                seen.add(raw_slug)
                if len(subs) >= max_subs:
                    return subs

    # 4. Templates (if no other subskills found)
    if not subs:
        tdir = os.path.join(skill_root, 'templates')
        if os.path.isdir(tdir):
            for f in sorted(os.listdir(tdir)):
                if f.endswith('.md') and not f.startswith('.'):
                    slug = f[:-3]
                    title = slug.replace('-', ' ').title()
                    subs.append({
                        'id': f'{skill_name}-{slug}',
                        'label': title,
                        'type': 'subskill',
                        'category': cat,
                        'parent': skill_name,
                        'desc': f'{skill_name} template: {title}'
                    })
                    seen.add(slug)
                    if len(subs) >= max_subs:
                        return subs

    return subs

def get_skills_graph():
    nodes = []
    links = []
    nodes.append({'id': 'core', 'label': 'HERMES', 'type': 'core', 'category': 'core', 'desc': 'Autonomous AI Engine & Core Brain'})
    cats_found = set()

    target_dir = SKILLS_DIR
    if not os.path.exists(target_dir) or not os.listdir(target_dir):
        # Fallback to local skills_graph.json if available
        fallback_file = os.path.join(BASE_DIR, 'skills_graph.json')
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if 'SKILL.md' in files:
            rel = os.path.relpath(root, target_dir)
            parts = rel.split(os.sep)
            cat = parts[0]
            skill_name = parts[-1]
            cats_found.add(cat)
            
            skill_path = os.path.join(root, 'SKILL.md')
            desc = ''
            try:
                with open(skill_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2048)
                    m = re.search(r'description:\s*([^\n\r]+)', content)
                    if m:
                        desc = m.group(1).strip(' \"\'')
            except Exception:
                pass
            if not desc:
                desc = f'Operational module for {skill_name}'
                
            node_type = 'agent' if cat == 'autonomous-ai-agents' and skill_name in ('claude-code', 'codex', 'antigravity', 'opencode', 'vibe', 'computer-use', 'hermes-agent') else 'skill'
            nodes.append({
                'id': skill_name,
                'label': skill_name,
                'type': node_type,
                'category': cat,
                'desc': desc
            })
            links.append({'source': cat, 'target': skill_name, 'value': 1})

            # Auto-detect all subskills/sub-modules underneath this skill
            for s in discover_subskills(root, skill_name, cat):
                nodes.append(s)
                links.append({'source': skill_name, 'target': s['id'], 'value': 1})

    for cat in sorted(cats_found):
        nodes.append({
            'id': cat,
            'label': cat.upper().replace('-', ' '),
            'type': 'cluster',
            'category': cat,
            'desc': f'Cluster category: {cat}'
        })
        links.append({'source': 'core', 'target': cat, 'value': 4})

    # Universal Automatic Detection of The Agency Specialists
    agents_candidates = [
        os.path.join(target_dir, '.agents.json'),
        os.path.join(BASE_DIR, 'agents.json'),
        '/opt/data/plugins/agency-agents-router/data/agents.json',
        '/plugins/agency-agents-router/data/agents.json',
    ]
    raw_agents = []
    for cand in agents_candidates:
        if os.path.exists(cand):
            try:
                with open(cand, 'r', encoding='utf-8') as afp:
                    raw_agents = json.load(afp)
                    if raw_agents:
                        break
            except Exception:
                pass

    if raw_agents:
        div_map = {
            'specialized': 'agency-orchestration',
            'engineering': 'agency-engineering',
            'testing': 'agency-qa-security',
            'security': 'agency-qa-security',
            'product': 'agency-product-design',
            'design': 'agency-product-design',
            'project-management': 'agency-product-design',
            'marketing': 'agency-growth',
            'sales': 'agency-growth',
            'paid-media': 'agency-growth',
            'academic': 'agency-domain',
            'research': 'agency-domain',
            'finance': 'agency-domain',
            'game-development': 'agency-domain',
            'gis': 'agency-domain',
            'healthcare': 'agency-domain',
            'spatial-computing': 'agency-domain',
            'support': 'agency-domain',
        }

        agency_cluster_defs = {
            'agency-orchestration': {'label': 'AGENCY ARCHITECTURE', 'desc': 'Orchestrator, workflow, and agentic identity specialists'},
            'agency-engineering': {'label': 'AGENCY ENGINEERING', 'desc': 'Fullstack, backend, DB, and DevOps specialist agents'},
            'agency-qa-security': {'label': 'AGENCY QA & SECURITY', 'desc': 'Evidence collector QA, regression testers, and security hardeners'},
            'agency-product-design': {'label': 'AGENCY PRODUCT & DESIGN', 'desc': 'Product managers, UX/UI, and design token architects'},
            'agency-growth': {'label': 'AGENCY GROWTH & REVENUE', 'desc': 'Agentic search optimizers, content strategists, and marketing specialists'},
            'agency-domain': {'label': 'AGENCY DOMAIN SPECIALISTS', 'desc': 'Spatial, healthcare, GIS, game dev, and academic research specialists'},
        }

        agency_cats_used = set()
        for a in raw_agents:
            ag_div = a.get('division', 'specialized')
            ag_cat = div_map.get(ag_div, 'agency-domain')
            agency_cats_used.add(ag_cat)

            ag_slug = a.get('slug') or a.get('name', '').lower().replace(' ', '-')
            ag_name = a.get('name', ag_slug)
            ag_desc = a.get('vibe') or a.get('description', f'Agency specialist: {ag_name}')

            nodes.append({
                'id': ag_slug,
                'label': ag_name,
                'type': 'agent',
                'category': ag_cat,
                'division': ag_div,
                'desc': ag_desc,
                'source_path': a.get('source_path', '')
            })
            links.append({'source': ag_cat, 'target': ag_slug, 'value': 1})

        for acat in sorted(agency_cats_used):
            cdef = agency_cluster_defs.get(acat, {'label': acat.upper().replace('-', ' '), 'desc': f'Agency category: {acat}'})
            nodes.append({
                'id': acat,
                'label': cdef['label'],
                'type': 'cluster',
                'category': acat,
                'desc': cdef['desc']
            })
            links.append({'source': 'core', 'target': acat, 'value': 4})

    return {'nodes': nodes, 'links': links, 'colors': category_colors}

def broadcast_event(data):
    msg = f"data: {json.dumps(data)}\n\n".encode('utf-8')
    with clients_lock:
        to_remove = []
        for wfile in clients:
            try:
                wfile.write(msg)
                wfile.flush()
            except Exception:
                to_remove.append(wfile)
        for dead in to_remove:
            if dead in clients:
                clients.remove(dead)

def event_watcher():
    last_mtime = 0
    while True:
        try:
            if os.path.exists(ACTIVE_EVENT_FILE):
                mtime = os.path.getmtime(ACTIVE_EVENT_FILE)
                if mtime != last_mtime:
                    last_mtime = mtime
                    with open(ACTIVE_EVENT_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    broadcast_event(data)
        except Exception:
            pass
        time.sleep(0.3)


def usage_watcher():
    """Watch .usage.json — fires activate/deactivate SSE whenever bump_use runs (any subagent)."""
    last_mtime = 0
    first_run = True
    deactivate_timers: dict = {}   # skill_name -> threading.Timer

    def _deactivate(skill_name):
        with _usage_lock:
            if skill_name in _usage_active:
                del _usage_active[skill_name]
        broadcast_event({'type': 'skill_deactivated', 'skill': skill_name})

    while True:
        try:
            if os.path.exists(USAGE_JSON):
                mtime = os.path.getmtime(USAGE_JSON)
                if mtime != last_mtime or first_run:
                    last_mtime = mtime
                    first_run = False
                    with open(USAGE_JSON, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    now_str = time.strftime('%Y-%m-%dT', time.gmtime())
                    for skill_name, rec in data.items():
                        used_at = rec.get('last_used_at', '')
                        if not used_at:
                            continue
                        # Only care about skills used in the last 30 seconds
                        try:
                            import datetime
                            dt = datetime.datetime.fromisoformat(used_at.replace('Z', '+00:00'))
                            age = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
                            if age > 30:
                                continue
                        except Exception:
                            continue

                        with _usage_lock:
                            prev = _usage_active.get(skill_name)
                            if prev != used_at:
                                _usage_active[skill_name] = used_at
                                # Cancel pending deactivation if any
                                old_timer = deactivate_timers.pop(skill_name, None)
                                if old_timer:
                                    old_timer.cancel()
                                # Broadcast activate
                                broadcast_event({'type': 'skill_activated', 'skill': skill_name})
                                # Schedule deactivation
                                t = threading.Timer(DEACTIVATE_DELAY, _deactivate, args=[skill_name])
                                t.daemon = True
                                t.start()
                                deactivate_timers[skill_name] = t
        except Exception:
            pass
        time.sleep(0.5)

class GalaxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        # Prevent browser caching of HTML/JS so updates take effect immediately
        if hasattr(self, 'path') and self.path in ('/', '/index.html'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        if self.path.startswith('/api/active'):
            # Polling endpoint — returns currently active skills with use_count & total skills count
            try:
                usage_data = {}
                if os.path.exists(USAGE_JSON):
                    with open(USAGE_JSON, 'r', encoding='utf-8') as f:
                        usage_data = json.load(f)
            except Exception:
                usage_data = {}
            with _usage_lock:
                active = list(_usage_active.keys())
            skills_info = []
            for s in active:
                use_count = usage_data.get(s, {}).get('use_count', 1)
                skills_info.append({'name': s, 'use_count': use_count})

            # Quick scan of total skills count (ignoring hidden dirs)
            total_skills = 0
            if os.path.exists(SKILLS_DIR):
                for _, dirs, files in os.walk(SKILLS_DIR):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    if 'SKILL.md' in files:
                        total_skills += 1

            payload = {'skills': active, 'skills_info': skills_info, 'total_skills': total_skills}
            content = json.dumps(payload).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if self.path.startswith('/api/graph'):
            data = get_skills_graph()
            content = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if self.path == '/api/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            with clients_lock:
                clients.append(self.wfile)

            try:
                self.wfile.write(b"data: {\"type\": \"connected\"}\n\n")
                self.wfile.flush()
                while True:
                    time.sleep(15)
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except Exception:
                pass
            finally:
                with clients_lock:
                    if self.wfile in clients:
                        clients.remove(self.wfile)
            return

        # Explicitly serve index.html for root /
        if self.path in ('/', '', '/index.html'):
            index_path = os.path.join(BASE_DIR, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        super().do_GET()

    def do_POST(self):
        if self.path in ('/api/activate', '/api/deactivate'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(body)
                raw_skills = payload.get('skills', [])
                if isinstance(raw_skills, list) and raw_skills:
                    skills_to_act = [s for s in raw_skills if s]
                elif payload.get('skill'):
                    skills_to_act = [payload.get('skill')]
                else:
                    skills_to_act = []

                if self.path == '/api/activate' and skills_to_act:
                    now_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                    with _usage_lock:
                        for sn in skills_to_act:
                            _usage_active[sn] = now_str
                    # Auto-deactivate after delay
                    def _auto_deact_all(slist=list(skills_to_act)):
                        time.sleep(DEACTIVATE_DELAY)
                        with _usage_lock:
                            for sn in slist:
                                _usage_active.pop(sn, None)
                        for sn in slist:
                            broadcast_event({'type': 'skill_deactivated', 'skill': sn})
                    threading.Thread(target=_auto_deact_all, daemon=True).start()
                    for sn in skills_to_act:
                        broadcast_event({'type': 'skill_activated', 'skill': sn})
                elif self.path == '/api/deactivate' and skills_to_act:
                    with _usage_lock:
                        for sn in skills_to_act:
                            _usage_active.pop(sn, None)
                    for sn in skills_to_act:
                        broadcast_event({'type': 'skill_deactivated', 'skill': sn})
                else:
                    broadcast_event(payload)

                # Persist to active_skill.json
                with open(ACTIVE_EVENT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(payload, f)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
            return
        self.send_response(404)
        self.end_headers()

def run_server():
    server = ThreadingHTTPServer(('0.0.0.0', PORT), GalaxyHandler)
    print(f"Galaxy Server listening on port {PORT} serving {BASE_DIR}")
    server.serve_forever()

if __name__ == '__main__':
    t = threading.Thread(target=event_watcher, daemon=True)
    t.start()
    t2 = threading.Thread(target=usage_watcher, daemon=True)
    t2.start()
    run_server()
