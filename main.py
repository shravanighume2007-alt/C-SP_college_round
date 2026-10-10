import sqlite3
from fastapi import FastAPI, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
import uvicorn

app = FastAPI(title="NEXUS Business Suite")
DB_NAME = "database.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # CRM Leads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT DEFAULT 'New'
            )
        """)
        # Marketing Campaigns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                channel TEXT NOT NULL,
                budget REAL NOT NULL,
                status TEXT DEFAULT 'Active'
            )
        """)
        # Webinars
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webinars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                speaker TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        # AI Workflow Requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instruction TEXT NOT NULL,
                status TEXT DEFAULT 'Pending Approval'
            )
        """)
        # Website Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('company_name', 'NEXUS')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme_color', '#0f172a')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('slogan', 'Manage your business from one intelligent workspace.')")
        conn.commit()

init_db()

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company_name }} - Business Suite</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8fafc;
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
            overflow-x: hidden;
        }
        /* Sidebar Styling */
        .sidebar {
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            width: 260px;
            background-color: #0d1b2a;
            color: #ffffff;
            z-index: 100;
            padding: 20px 15px;
            display: flex;
            flex-direction: column;
        }
        .sidebar-brand {
            font-size: 1.4rem;
            font-weight: 800;
            letter-spacing: 1px;
            color: #ffffff;
            text-decoration: none;
            margin-bottom: 2rem;
            padding-left: 10px;
        }
        .sidebar-nav {
            list-style: none;
            padding: 0;
            margin: 0;
            flex-grow: 1;
        }
        .sidebar-nav .nav-item {
            margin-bottom: 0.5rem;
        }
        .sidebar-nav .nav-link {
            color: #94a3b8;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .sidebar-nav .nav-link:hover, .sidebar-nav .nav-link.active {
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.08);
        }
        /* Main Content Area */
        .main-content {
            margin-left: 260px;
            padding: 30px;
            min-height: 100vh;
        }
        .top-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 15px;
        }
        .workspace-badge {
            font-size: 0.85rem;
            font-weight: 600;
            color: #0f172a;
            background: #ffffff;
            padding: 6px 14px;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card {
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        .btn-primary {
            background-color: #2563eb;
            border-color: #2563eb;
            border-radius: 8px;
            font-weight: 500;
        }
        .btn-primary:hover {
            background-color: #1d4ed8;
            border-color: #1d4ed8;
        }
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <div class="sidebar">
        <a href="/" class="sidebar-brand">NEXUS<span class="text-primary">.</span></a>
        <ul class="sidebar-nav">
            <li class="nav-item"><a class="nav-link {% if active_page == 'dashboard' %}active{% endif %}" href="/"><i class="bi bi-grid-1x2-fill"></i> Overview</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'builder' %}active{% endif %}" href="/builder"><i class="bi bi-globe"></i> Website Builder</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'crm' %}active{% endif %}" href="/crm"><i class="bi bi-people-fill"></i> CRM & Leads</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'marketing' %}active{% endif %}" href="/marketing"><i class="bi bi-megaphone-fill"></i> Marketing</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'webinars' %}active{% endif %}" href="/webinars"><i class="bi bi-camera-video-fill"></i> Webinars</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'subscriptions' %}active{% endif %}" href="/subscriptions"><i class="bi bi-credit-card-fill"></i> Subscriptions</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'workflow' %}active{% endif %}" href="/workflow"><i class="bi bi-robot"></i> AI Business Agent</a></li>
            <li class="nav-item"><a class="nav-link {% if active_page == 'analytics' %}active{% endif %}" href="/analytics"><i class="bi bi-bar-chart-fill"></i> Analytics</a></li>
        </ul>
    </div>

    <!-- Main Content Container -->
    <div class="main-content">
        <div class="top-header">
            <h5 class="fw-bold text-secondary mb-0">Business Overview</h5>
            <div class="workspace-badge">
                <span style="height: 8px; width: 8px; background-color: #22c55e; border-radius: 50%; display: inline-block;"></span> 
                Nexus demo workspace
            </div>
        </div>

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        leads_count = cursor.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        campaigns_count = cursor.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        webinars_count = cursor.execute("SELECT COUNT(*) FROM webinars").fetchone()[0]
        workflows_count = cursor.execute("SELECT COUNT(*) FROM workflows WHERE status='Pending Approval'").fetchone()[0]
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <div class="mb-4">
        <h1 class="display-6 fw-bold text-dark">Everything. Connected.</h1>
        <p class="text-muted">{{ slogan }}</p>
    </div>
    
    <!-- Stat Cards Row -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card p-3">
                <span class="text-muted small fw-semibold">CRM Leads</span>
                <h2 class="fw-bold mt-1 mb-0">{{ leads_count }}</h2>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-3">
                <span class="text-muted small fw-semibold">Campaigns</span>
                <h2 class="fw-bold mt-1 mb-0">{{ campaigns_count }}</h2>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-3">
                <span class="text-muted small fw-semibold">Webinars</span>
                <h2 class="fw-bold mt-1 mb-0">{{ webinars_count }}</h2>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-3">
                <span class="text-muted small fw-semibold">Pending Approvals</span>
                <h2 class="fw-bold mt-1 mb-0 text-warning">{{ workflows_count }}</h2>
            </div>
        </div>
    </div>

    <!-- Workspace Modules Grid -->
    <h5 class="fw-bold text-dark mb-3">Your Workspace</h5>
    <div class="row g-4 mb-4">
        <div class="col-md-4">
            <div class="card p-4 h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark"><i class="bi bi-globe text-primary me-2"></i>Website Builder</h5>
                    <p class="text-muted small mt-2">Customize a landing page preview.</p>
                </div>
                <div><a href="/builder" class="btn btn-sm btn-light border text-primary fw-semibold mt-3">Open module &rarr;</a></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark"><i class="bi bi-people-fill text-primary me-2"></i>Intelligent CRM</h5>
                    <p class="text-muted small mt-2">Save and track potential customers.</p>
                </div>
                <div><a href="/crm" class="btn btn-sm btn-light border text-primary fw-semibold mt-3">Open module &rarr;</a></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark"><i class="bi bi-megaphone-fill text-primary me-2"></i>Marketing</h5>
                    <p class="text-muted small mt-2">Create campaign drafts.</p>
                </div>
                <div><a href="/marketing" class="btn btn-sm btn-light border text-primary fw-semibold mt-3">Open module &rarr;</a></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark"><i class="bi bi-camera-video-fill text-primary me-2"></i>Webinars</h5>
                    <p class="text-muted small mt-2">Create events and track registrations.</p>
                </div>
                <div><a href="/webinars" class="btn btn-sm btn-light border text-primary fw-semibold mt-3">Open module &rarr;</a></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark"><i class="bi bi-credit-card-fill text-primary me-2"></i>SaaS Billing</h5>
                    <p class="text-muted small mt-2">Review demo subscription plans.</p>
                </div>
                <div><a href="/subscriptions" class="btn btn-sm btn-light border text-primary fw-semibold mt-3">Open module &rarr;</a></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark"><i class="bi bi-robot text-primary me-2"></i>AI Business Agent</h5>
                    <p class="text-muted small mt-2">Prepare multi-step workflows for approval.</p>
                </div>
                <div><a href="/workflow" class="btn btn-sm btn-light border text-primary fw-semibold mt-3">Open module &rarr;</a></div>
            </div>
        </div>
    </div>

    <!-- Connected Workflow Footer Card -->
    <div class="card p-4 mb-4">
        <h6 class="fw-bold text-dark">Connected workflow</h6>
        <p class="text-muted small mb-2">Capture lead &rarr; Prepare campaign &rarr; Create webinar &rarr; Review follow-up plan.</p>
        <span class="text-muted" style="font-size: 0.75rem;">External messages and payments are not sent by this prototype.</span>
    </div>
    """

    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="dashboard",
        slogan=settings.get("slogan", ""),
        leads_count=leads_count,
        campaigns_count=campaigns_count,
        webinars_count=webinars_count,
        workflows_count=workflows_count
    )
    return HTMLResponse(content=rendered)

@app.get("/builder", response_class=HTMLResponse)
def builder_get() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">Website Builder</h3>
    <div class="row">
        <div class="col-md-5">
            <div class="card p-4">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Company Name</label>
                        <input type="text" class="form-control" name="company_name" value="{{ company_name }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Slogan</label>
                        <input type="text" class="form-control" name="slogan" value="{{ slogan }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Theme Color</label>
                        <input type="color" class="form-control form-control-color" name="theme_color" value="{{ theme_color }}">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Save & Publish Changes</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card p-4 bg-white">
                <h5 class="text-muted small mb-3">Live Sample Website Preview</h5>
                <div class="p-5 border rounded text-center bg-light">
                    <h1 class="fw-bold" style="color: {{ theme_color }};">{{ company_name }}</h1>
                    <p class="lead text-secondary mt-2">{{ slogan }}</p>
                    <button class="btn btn-primary mt-3">Get Started Today</button>
                </div>
            </div>
        </div>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="builder",
        theme_color=settings.get("theme_color", "#0f172a"),
        slogan=settings.get("slogan", "")
    )
    return HTMLResponse(content=rendered)

@app.post("/builder", response_class=HTMLResponse)
def builder_post(company_name: str = Form(...), slogan: str = Form(...), theme_color: str = Form(...)) -> RedirectResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'company_name'", (company_name,))
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'theme_color'", (theme_color,))
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'slogan'", (slogan,))
        conn.commit()
    return RedirectResponse(url="/builder", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/crm", response_class=HTMLResponse)
def crm_get() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        leads = cursor.execute("SELECT id, name, email, status FROM leads").fetchall()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">Intelligent CRM & Leads</h3>
    <div class="row">
        <div class="col-md-4">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Add New Lead</h5>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Full Name</label>
                        <input type="text" class="form-control" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Email Address</label>
                        <input type="email" class="form-control" name="email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Lead Status</label>
                        <select class="form-select" name="status">
                            <option value="New">New</option>
                            <option value="Contacted">Contacted</option>
                            <option value="Converted">Converted</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Add Lead</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Customer Leads Database</h5>
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lead in leads %}
                        <tr>
                            <td>{{ lead[0] }}</td>
                            <td>{{ lead[1] }}</td>
                            <td>{{ lead[2] }}</td>
                            <td><span class="badge bg-secondary">{{ lead[3] }}</span></td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="text-center text-muted">No leads found in database.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="crm",
        leads=leads
    )
    return HTMLResponse(content=rendered)

@app.post("/crm", response_class=HTMLResponse)
def crm_post(name: str = Form(...), email: str = Form(...), status: str = Form(...)) -> RedirectResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO leads (name, email, status) VALUES (?, ?, ?)", (name, email, status))
        conn.commit()
    return RedirectResponse(url="/crm", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/marketing", response_class=HTMLResponse)
def marketing_get() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        campaigns = cursor.execute("SELECT id, title, channel, budget, status FROM campaigns").fetchall()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">Marketing Campaigns</h3>
    <div class="row">
        <div class="col-md-4">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Create Campaign</h5>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Campaign Title</label>
                        <input type="text" class="form-control" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Channel</label>
                        <input type="text" class="form-control" name="channel" placeholder="e.g. Google Ads, Meta" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Budget ($)</label>
                        <input type="number" step="0.01" class="form-control" name="budget" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Launch Campaign</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Active Marketing Campaigns</h5>
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Channel</th>
                            <th>Budget</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for camp in campaigns %}
                        <tr>
                            <td>{{ camp[0] }}</td>
                            <td>{{ camp[1] }}</td>
                            <td>{{ camp[2] }}</td>
                            <td>${{ "%.2f"|format(camp[3]) }}</td>
                            <td><span class="badge bg-success">{{ camp[4] }}</span></td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" class="text-center text-muted">No campaigns created yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="marketing",
        campaigns=campaigns
    )
    return HTMLResponse(content=rendered)

@app.post("/marketing", response_class=HTMLResponse)
def marketing_post(title: str = Form(...), channel: str = Form(...), budget: float = Form(...)) -> RedirectResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO campaigns (title, channel, budget) VALUES (?, ?, ?)", (title, channel, budget))
        conn.commit()
    return RedirectResponse(url="/marketing", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/webinars", response_class=HTMLResponse)
def webinars_get() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        webinars_list = cursor.execute("SELECT id, title, speaker, date FROM webinars").fetchall()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">Webinars & Events</h3>
    <div class="row">
        <div class="col-md-4">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Schedule Webinar</h5>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Webinar Title</label>
                        <input type="text" class="form-control" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Speaker</label>
                        <input type="text" class="form-control" name="speaker" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Date & Time</label>
                        <input type="datetime-local" class="form-control" name="date" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Schedule Event</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Scheduled Webinars</h5>
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Speaker</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for web in webinars_list %}
                        <tr>
                            <td>{{ web[0] }}</td>
                            <td>{{ web[1] }}</td>
                            <td>{{ web[2] }}</td>
                            <td>{{ web[3] }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="text-center text-muted">No webinars scheduled.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="webinars",
        webinars_list=webinars_list
    )
    return HTMLResponse(content=rendered)

@app.post("/webinars", response_class=HTMLResponse)
def webinars_post(title: str = Form(...), speaker: str = Form(...), date: str = Form(...)) -> RedirectResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO webinars (title, speaker, date) VALUES (?, ?, ?)", (title, speaker, date))
        conn.commit()
    return RedirectResponse(url="/webinars", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_get(subscribers: int = 120, price: float = 29.0, churn: float = 5.0) -> HTMLResponse:
    mrr = subscribers * price
    arr = mrr * 12

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">SaaS Billing & Subscriptions</h3>
    <div class="row">
        <div class="col-md-5">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Subscription Revenue Calculator</h5>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Active Subscribers</label>
                        <input type="number" class="form-control" name="subscribers" value="{{ subscribers }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Monthly Price per User ($)</label>
                        <input type="number" step="0.01" class="form-control" name="price" value="{{ price }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Estimated Monthly Churn Rate (%)</label>
                        <input type="number" step="0.1" class="form-control" name="churn" value="{{ churn }}" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Calculate Revenue</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card p-4 bg-white">
                <h5 class="fw-bold mb-3">Revenue Metrics Overview</h5>
                <hr>
                <div class="row text-center">
                    <div class="col-6 mb-4">
                        <span class="text-muted small">Monthly Recurring Revenue (MRR)</span>
                        <h2 class="text-success fw-bold">${{ "%.2f"|format(mrr) }}</h2>
                    </div>
                    <div class="col-6 mb-4">
                        <span class="text-muted small">Annual Recurring Revenue (ARR)</span>
                        <h2 class="text-primary fw-bold">${{ "%.2f"|format(arr) }}</h2>
                    </div>
                    <div class="col-12">
                        <div class="alert alert-info py-2 small">
                            Estimated churn impact: ~{{ churn }}% monthly subscriber loss.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="subscriptions",
        subscribers=subscribers,
        price=price,
        churn=churn,
        mrr=mrr,
        arr=arr
    )
    return HTMLResponse(content=rendered)

@app.post("/subscriptions", response_class=HTMLResponse)
def subscriptions_post(subscribers: int = Form(...), price: float = Form(...), churn: float = Form(...)) -> RedirectResponse:
    return RedirectResponse(url=f"/subscriptions?subscribers={subscribers}&price={price}&churn={churn}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/workflow", response_class=HTMLResponse)
def workflow_get() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        workflows = cursor.execute("SELECT id, instruction, status FROM workflows").fetchall()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">AI Business Agent & Workflows</h3>
    <div class="row">
        <div class="col-md-5">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">AI Workflow Assistant</h5>
                <p class="text-muted small">Instruct the AI to execute simulated actions across your business modules.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Workflow Instruction</label>
                        <textarea class="form-control" name="instruction" rows="3" placeholder="Enter business action instruction..." required></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Request AI Action</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card p-4">
                <h5 class="fw-bold mb-3">Workflow Approval Queue</h5>
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Instruction</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for wf in workflows %}
                        <tr>
                            <td>{{ wf[0] }}</td>
                            <td>{{ wf[1] }}</td>
                            <td>
                                {% if wf[2] == 'Pending Approval' %}
                                <span class="badge bg-warning text-dark">{{ wf[2] }}</span>
                                {% elif wf[2] == 'Approved & Executed' %}
                                <span class="badge bg-success">{{ wf[2] }}</span>
                                {% else %}
                                <span class="badge bg-danger">{{ wf[2] }}</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if wf[2] == 'Pending Approval' %}
                                <form method="POST" class="d-inline">
                                    <input type="hidden" name="action" value="approve">
                                    <input type="hidden" name="id" value="{{ wf[0] }}">
                                    <button type="submit" class="btn btn-success btn-sm">Approve</button>
                                </form>
                                <form method="POST" class="d-inline">
                                    <input type="hidden" name="action" value="reject">
                                    <input type="hidden" name="id" value="{{ wf[0] }}">
                                    <button type="submit" class="btn btn-outline-danger btn-sm">Reject</button>
                                </form>
                                {% else %}
                                <span class="text-muted small">Completed</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="text-center text-muted">No workflows queued.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="workflow",
        workflows=workflows
    )
    return HTMLResponse(content=rendered)

@app.post("/workflow", response_class=HTMLResponse)
def workflow_post(action: str = Form(...), instruction: str | None = Form(None), id: int | None = Form(None)) -> RedirectResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if action == "add" and instruction:
            cursor.execute("INSERT INTO workflows (instruction, status) VALUES (?, 'Pending Approval')", (instruction,))
        elif action == "approve" and id is not None:
            cursor.execute("UPDATE workflows SET status = 'Approved & Executed' WHERE id = ?", (id,))
        elif action == "reject" and id is not None:
            cursor.execute("UPDATE workflows SET status = 'Rejected' WHERE id = ?", (id,))
        conn.commit()
    return RedirectResponse(url="/workflow", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/analytics", response_class=HTMLResponse)
def analytics_get() -> HTMLResponse:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

    content_template = """
    <h3 class="fw-bold text-dark mb-4">Analytics & Reports</h3>
    <div class="card p-5 text-center">
        <h4 class="text-secondary">Performance Insights</h4>
        <p class="text-muted">Real-time charts and workspace analytics will appear here.</p>
    </div>
    """
    html = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", f"{{% block content %}} {content_template} {{% endblock %}}")
    rendered = Template(html).render(
        company_name=settings.get("company_name", "NEXUS"),
        active_page="analytics"
    )
    return HTMLResponse(content=rendered)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
