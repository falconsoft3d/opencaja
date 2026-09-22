#!/bin/sh
set -e

if [ "$SECRET_KEY" = "" ] || [ "$SECRET_KEY" = "dev-secret-key-change-me" ]; then
  echo "ADVERTENCIA: define la variable de entorno SECRET_KEY con un valor propio en producción."
fi

flask init-db

if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  python <<'PYEOF'
import os

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    username = os.environ["ADMIN_USERNAME"]
    if User.query.filter_by(username=username).first():
        print(f"Usuario admin '{username}' ya existe, se omite.")
    else:
        user = User(username=username, email=os.environ["ADMIN_EMAIL"], is_admin=True)
        user.set_password(os.environ["ADMIN_PASSWORD"])
        db.session.add(user)
        db.session.commit()
        print(f"Usuario admin '{username}' creado.")
PYEOF
fi

exec "$@"
