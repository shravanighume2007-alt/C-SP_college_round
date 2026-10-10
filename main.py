import sqlite3
from fastapi import FastAPI, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
import uvicorn

app = FastAPI(title="Business Suite Application")
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
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('company_name',"
        " 'Acme Corp')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('theme_color',"
        " '#0d6efd')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('slogan',"
        " 'Empowering your business growth')"
    )
    conn.commit()


# Initialize database on startup
init_db()

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company_name }} - Business Suite</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --primary-color: {{ theme_color }}; }
        .bg-primary { background-color: var(--primary-color) !important; }
        .text-primary { color: var(--primary-color) !important; }
        .btn-primary { background-color: var(--primary-color); border-color: var(--primary-color); }
        .btn-primary:hover { opacity: 0.9; background-color: var(--primary-color); border-color: var(--primary-color); }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div class="container-fluid">
            <a class="navbar-brand fw-bold" href="/">🚀 {{ company_name }}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/builder">Website Builder</a></li>
                    <li class="nav-item"><a class="nav-link" href="/crm">CRM</a></li>
                    <li class="nav-item"><a class="nav-link" href="/marketing">Marketing</a></li>
                    <li class="nav-item"><a class="nav-link" href="/webinars">Webinars</a></li>
                    <li class="nav-item"><a class="nav-link" href="/subscriptions">Subscriptions</a></li>
                    <li class="nav-item"><a class="nav-link" href="/workflow">AI Workflow</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container my-4">
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
    leads_count = cursor.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]
    campaigns_count = cursor.execute(
        "SELECT COUNT(*) FROM campaigns"
    ).fetchone()[0]
    webinars_count = cursor.execute(
        "SELECT COUNT(*) FROM webinars"
    ).fetchone()[0]
    workflows_count = cursor.execute(
        "SELECT COUNT(*) FROM workflows WHERE status='Pending Approval'"
    ).fetchone()[0]
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row mb-4">
        <div class="col-12">
            <div class="p-5 mb-4 bg-white rounded-3 shadow-sm border">
                <h1 class="display-5 fw-bold text-primary">Business Overview</h1>
                <p class="fs-4 text-muted">{{ slogan }}</p>
                <hr class="my-4">
                <p>Welcome to your centralized operations center. Manage leads, review campaigns, schedule webinars, and control AI workflows seamlessly.</p>
            </div>
        </div>
    </div>
    
    <div class="row text-center g-4">
        <div class="col-md-3">
            <div class="card shadow-sm border-0 py-3">
                <div class="card-body">
                    <h5 class="card-title text-muted">Total Leads</h5>
                    <h2 class="fw-bold text-primary">{{ leads_count }}</h2>
                    <a href="/crm" class="btn btn-outline-primary btn-sm mt-2">Manage CRM</a>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card shadow-sm border-0 py-3">
                <div class="card-body">
                    <h5 class="card-title text-muted">Active Campaigns</h5>
                    <h2 class="fw-bold text-primary">{{ campaigns_count }}</h2>
                    <a href="/marketing" class="btn btn-outline-primary btn-sm mt-2">View Campaigns</a>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card shadow-sm border-0 py-3">
                <div class="card-body">
                    <h5 class="card-title text-muted">Webinars</h5>
                    <h2 class="fw-bold text-primary">{{ webinars_count }}</h2>
                    <a href="/webinars" class="btn btn-outline-primary btn-sm mt-2">Manage Webinars</a>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card shadow-sm border-0 py-3">
                <div class="card-body">
                    <h5 class="card-title text-muted">Pending AI Actions</h5>
                    <h2 class="fw-bold text-warning">{{ workflows_count }}</h2>
                    <a href="/workflow" class="btn btn-outline-warning btn-sm mt-2">Review Requests</a>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
  )

  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      slogan=settings.get("slogan", ""),
      leads_count=leads_count,
      campaigns_count=campaigns_count,
      webinars_count=webinars_count,
      workflows_count=workflows_count,
  )
  return HTMLResponse(content=rendered)


@app.get("/builder", response_class=HTMLResponse)
def builder_get() -> HTMLResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row">
        <div class="col-md-5">
            <div class="card shadow-sm border-0 p-4">
                <h3 class="mb-3 text-primary">Website Builder</h3>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Company Name</label>
                        <input type="text" class="form-control" name="company_name" value="{{ company_name }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Slogan</label>
                        <input type="text" class="form-control" name="slogan" value="{{ slogan }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Theme Color</label>
                        <input type="color" class="form-control form-control-color" name="theme_color" value="{{ theme_color }}">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Save & Publish Changes</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card shadow-sm border-0 p-4 bg-white">
                <h5 class="text-muted mb-3">Live Sample Website Preview</h5>
                <div class="p-5 border rounded text-center" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);">
                    <h1 class="fw-bold" style="color: {{ theme_color }};">{{ company_name }}</h1>
                    <p class="lead text-secondary mt-2">{{ slogan }}</p>
                    <button class="btn btn-primary mt-3">Get Started Today</button>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
  )
  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      slogan=settings.get("slogan", ""),
  )
  return HTMLResponse(content=rendered)


@app.post("/builder", response_class=HTMLResponse)
def builder_post(
    company_name: str = Form(...),
    slogan: str = Form(...),
    theme_color: str = Form(...),
) -> RedirectResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE settings SET value = ? WHERE key = 'company_name'",
        (company_name,),
    )
    cursor.execute(
        "UPDATE settings SET value = ? WHERE key = 'theme_color'",
        (theme_color,),
    )
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'slogan'", (slogan,))
    conn.commit()
  return RedirectResponse(url="/builder", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/crm", response_class=HTMLResponse)
def crm_get() -> HTMLResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    leads = cursor.execute("SELECT id, name, email, status FROM leads").fetchall()
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row">
        <div class="col-md-4">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Add New Lead</h4>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Full Name</label>
                        <input type="text" class="form-control" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email Address</label>
                        <input type="email" class="form-control" name="email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Lead Status</label>
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
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Customer Leads Database</h4>
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
    {% endblock %}
    """
  )
  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      leads=leads,
  )
  return HTMLResponse(content=rendered)


@app.post("/crm", response_class=HTMLResponse)
def crm_post(
    name: str = Form(...), email: str = Form(...), status: str = Form(...)
) -> RedirectResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leads (name, email, status) VALUES (?, ?, ?)",
        (name, email, status),
    )
    conn.commit()
  return RedirectResponse(url="/crm", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/marketing", response_class=HTMLResponse)
def marketing_get() -> HTMLResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    campaigns = cursor.execute(
        "SELECT id, title, channel, budget, status FROM campaigns"
    ).fetchall()
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row">
        <div class="col-md-4">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Create Campaign</h4>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Campaign Title</label>
                        <input type="text" class="form-control" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Channel</label>
                        <input type="text" class="form-control" name="channel" placeholder="e.g. Google Ads, Meta" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Budget ($)</label>
                        <input type="number" step="0.01" class="form-control" name="budget" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Launch Campaign</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Active Marketing Campaigns</h4>
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
    {% endblock %}
    """
  )
  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      campaigns=campaigns,
  )
  return HTMLResponse(content=rendered)


@app.post("/marketing", response_class=HTMLResponse)
def marketing_post(
    title: str = Form(...), channel: str = Form(...), budget: float = Form(...)
) -> RedirectResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO campaigns (title, channel, budget) VALUES (?, ?, ?)",
        (title, channel, budget),
    )
    conn.commit()
  return RedirectResponse(url="/marketing", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/webinars", response_class=HTMLResponse)
def webinars_get() -> HTMLResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    webinars_list = cursor.execute(
        "SELECT id, title, speaker, date FROM webinars"
    ).fetchall()
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row">
        <div class="col-md-4">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Schedule Webinar</h4>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Webinar Title</label>
                        <input type="text" class="form-control" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Speaker</label>
                        <input type="text" class="form-control" name="speaker" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Date & Time</label>
                        <input type="datetime-local" class="form-control" name="date" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Schedule Event</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Scheduled Webinars</h4>
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
    {% endblock %}
    """
  )
  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      webinars_list=webinars_list,
  )
  return HTMLResponse(content=rendered)


@app.post("/webinars", response_class=HTMLResponse)
def webinars_post(
    title: str = Form(...), speaker: str = Form(...), date: str = Form(...)
) -> RedirectResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO webinars (title, speaker, date) VALUES (?, ?, ?)",
        (title, speaker, date),
    )
    conn.commit()
  return RedirectResponse(url="/webinars", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_get(
    subscribers: int = 120, price: float = 29.0, churn: float = 5.0
) -> HTMLResponse:
  mrr = subscribers * price
  arr = mrr * 12

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row">
        <div class="col-md-5">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Subscription Revenue Calculator</h4>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Active Subscribers</label>
                        <input type="number" class="form-control" name="subscribers" value="{{ subscribers }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Monthly Price per User ($)</label>
                        <input type="number" step="0.01" class="form-control" name="price" value="{{ price }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Estimated Monthly Churn Rate (%)</label>
                        <input type="number" step="0.1" class="form-control" name="churn" value="{{ churn }}" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Calculate Revenue</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card shadow-sm border-0 p-4 bg-white">
                <h4 class="mb-3 text-primary">Revenue Metrics Overview</h4>
                <hr>
                <div class="row text-center">
                    <div class="col-6 mb-4">
                        <h6 class="text-muted">Monthly Recurring Revenue (MRR)</h6>
                        <h2 class="text-success fw-bold">${{ "%.2f"|format(mrr) }}</h2>
                    </div>
                    <div class="col-6 mb-4">
                        <h6 class="text-muted">Annual Recurring Revenue (ARR)</h6>
                        <h2 class="text-primary fw-bold">${{ "%.2f"|format(arr) }}</h2>
                    </div>
                    <div class="col-12">
                        <div class="alert alert-info py-2">
                            Estimated churn impact: ~{{ churn }}% monthly subscriber loss.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
  )
  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      subscribers=subscribers,
      price=price,
      churn=churn,
      mrr=mrr,
      arr=arr,
  )
  return HTMLResponse(content=rendered)


@app.post("/subscriptions", response_class=HTMLResponse)
def subscriptions_post(
    subscribers: int = Form(...), price: float = Form(...), churn: float = Form(...)
) -> RedirectResponse:
  return RedirectResponse(
      url=f"/subscriptions?subscribers={subscribers}&price={price}&churn={churn}",
      status_code=status.HTTP_303_SEE_OTHER,
  )


@app.get("/workflow", response_class=HTMLResponse)
def workflow_get() -> HTMLResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    workflows = cursor.execute(
        "SELECT id, instruction, status FROM workflows"
    ).fetchall()
    settings = dict(cursor.execute("SELECT key, value FROM settings").fetchall())

  html = (
      BASE_TEMPLATE
      + """
    {% block content %}
    <div class="row">
        <div class="col-md-5">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">AI Workflow Assistant</h4>
                <p class="text-muted small">Instruct the AI to execute simulated actions across your business modules.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="add">
                    <div class="mb-3">
                        <label class="form-label">Workflow Instruction</label>
                        <textarea class="form-control" name="instruction" rows="3" placeholder="Enter business action instruction..." required></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Request AI Action</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card shadow-sm border-0 p-4">
                <h4 class="mb-3 text-primary">Workflow Approval Queue</h4>
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
    {% endblock %}
    """
  )
  rendered = Template(html).render(
      company_name=settings.get("company_name", "Acme Corp"),
      theme_color=settings.get("theme_color", "#0d6efd"),
      workflows=workflows,
  )
  return HTMLResponse(content=rendered)


@app.post("/workflow", response_class=HTMLResponse)
def workflow_post(
    action: str = Form(...),
    instruction: str | None = Form(None),
    id: int | None = Form(None),
) -> RedirectResponse:
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    if action == "add" and instruction:
      cursor.execute(
          "INSERT INTO workflows (instruction, status) VALUES (?, 'Pending"
          " Approval')",
          (instruction,),
      )
    elif action == "approve" and id is not None:
      cursor.execute(
          "UPDATE workflows SET status = 'Approved & Executed' WHERE id = ?",
          (id,),
      )
    elif action == "reject" and id is not None:
      cursor.execute("UPDATE workflows SET status = 'Rejected' WHERE id = ?", (id,))
    conn.commit()
  return RedirectResponse(url="/workflow", status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
  uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
