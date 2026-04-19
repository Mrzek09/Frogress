from flask import render_template
from werkzeug.exceptions import HTTPException

def page_not_found(e):
    return render_template('errors/404.html', error=e), 404

def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html', error=e), 500