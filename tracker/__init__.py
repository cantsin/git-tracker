from flask import Flask, jsonify
from flask.ext.login import LoginManager
from flask.ext.cors import CORS
from werkzeug.exceptions import HTTPException, default_exceptions

# ugh. work around an internal bug with flask and python3.4
import pkgutil
old_loader = pkgutil.get_loader
def override_loader(*args, **kwargs):
    try:
        return old_loader(*args, **kwargs)
    except AttributeError: # pragma: no cover
        return None
pkgutil.get_loader = override_loader

# prevent werkzeug from emitting HTML errors.
def make_json_app(import_name, **kwargs):
    def make_json_error(ex):
        response = jsonify(success=False, error=str(ex))
        response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
        return response

    app = Flask(import_name, **kwargs)
    CORS(app)

    for code in default_exceptions.keys():
        app.error_handler_spec[None][code] = make_json_error

    return app

app = make_json_app('git-tracker')

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)

from .models import User
import tracker.views
