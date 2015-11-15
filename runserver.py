#!/usr/bin/env python

from flask import Flask

from src import app
from src.cron import scheduler
from src.models import init_db

if __name__ == '__main__':
    try:
        import config
        app.secret_key = config.secret_key
    except ImportError:
        import os
        app.secret_key = os.urandom(24)
    import sys
    app.debug = True
    app.config['version'] = '1.0'
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['DATABASE'] = 'sqlite:////tmp/test.db'
    init_db()
    scheduler.start()
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port)
