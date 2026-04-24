Hybrid Analyze Page
===================

What this is
------------
A new separate page that combines the strongest parts of:
- the main /analyze page
- the standalone public redaction page

Included features
-----------------
- text input + file upload
- detect PII + anonymize actions
- replace, redact, mask, hash, synthesize operators
- threshold slider
- entity selection with select all / clear all
- allowlist + denylist
- NER model selector
- linked hover original/result preview
- final output box
- KPI summary cards
- entity mix + confidence bands
- evidence table with recognizer + rationale toggle
- TXT + CSV downloads
- save session / load session / download session
- optional pipeline card attachment
- can run standalone or be mounted under the main app

Files
-----
- hybrid_redaction_app.py
- templates/hybrid_redaction.html
- static/hybrid_redaction.css
- static/hybrid_redaction.js

Standalone local test
---------------------
Copy the whole hybrid_redaction folder into your main project folder.
Then run:

    cd C:\Users\yeshp\Desktop\anonymous-studio-main\anonymous-studio-main
    .venv\Scripts\activate
    python hybrid_redaction\hybrid_redaction_app.py

Open:

    http://127.0.0.1:5052

Mount inside the main project later
-----------------------------------
In the Flask server used by the main app, register the blueprint:

    from hybrid_redaction.hybrid_redaction_app import create_blueprint
    flask_app.register_blueprint(create_blueprint(url_prefix="/hybrid-analyze"))

Then open:

    http://127.0.0.1:5000/hybrid-analyze

