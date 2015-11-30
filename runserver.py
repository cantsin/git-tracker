#!/usr/bin/env python

from flask import Flask

from tracker import app
from tracker.cron import scheduler
from tracker.models import init_db

import os
import sys

if __name__ == '__main__':
    try:
        import config
        app.secret_key = config.secret_key
    except ImportError:
        app.secret_key = os.urandom(24)
    base_dir = os.path.dirname(os.path.realpath(__file__))
    app.debug = True
    app.config['version'] = '2.0'
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads/')
    app.config['REPOSITORY_FOLDER'] = os.path.join(base_dir, 'repositories/')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    init_db()
    print('Database initialized.')
    scheduler.start()
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port)
