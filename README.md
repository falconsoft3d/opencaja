# opencaja

Aplicación web en Flask con login, dashboard y menú lateral, con CRUD para:

- Proyectos (código, nombre)
- Clientes (nombre, email, teléfono)
- Pagos de Cliente (secuencia, fecha, importe)
- Pagos a Proveedor (secuencia, fecha, importe)
- Perfil (cambio de contraseña)
- Usuarios (solo administradores pueden agregar/editar usuarios)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración inicial

```bash
export FLASK_APP=run.py
flask init-db          # crea las tablas
flask create-admin     # crea el primer usuario administrador
```

## Ejecutar

```bash
flask run
# o: python run.py
```

Abrir http://127.0.0.1:5000 e iniciar sesión con el usuario administrador creado.

## Producción con Docker

Guía completa paso a paso para instalarlo en un servidor Ubuntu: [DEPLOY.md](DEPLOY.md).

La imagen usa Gunicorn (no el servidor de desarrollo de Flask). El entrypoint crea las tablas
automáticamente al arrancar y, si se definen `ADMIN_USERNAME`/`ADMIN_EMAIL`/`ADMIN_PASSWORD`,
crea el usuario administrador la primera vez (en arranques posteriores lo omite si ya existe).

```bash
cp .env.example .env   # editar SECRET_KEY y credenciales del admin
docker compose up -d --build
```

Abrir http://localhost:8000. Los datos (SQLite) persisten en el volumen `opencaja_data`
(`/app/instance` dentro del contenedor).

Variables de entorno soportadas:

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Clave de firma de sesiones/CSRF. **Obligatoria en producción.** |
| `DATABASE_URL` | Cadena de conexión SQLAlchemy (por defecto SQLite en `instance/`). |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Si se definen las tres, crea el admin en el primer arranque. |

Con `docker` a secas (sin compose):

```bash
docker build -t opencaja .
docker run -d -p 8000:8000 \
  -e SECRET_KEY=cambia-esto \
  -e ADMIN_USERNAME=admin -e ADMIN_EMAIL=admin@example.com -e ADMIN_PASSWORD=cambia-esto \
  -v opencaja_data:/app/instance \
  opencaja
```

Nota: la base de datos por defecto es SQLite con un solo worker de Gunicorn (`--workers 1
--threads 4`), adecuado para uso interno con pocos usuarios concurrentes. Para más carga o alta
disponibilidad, apunta `DATABASE_URL` a Postgres/MySQL y aumenta `--workers`.
