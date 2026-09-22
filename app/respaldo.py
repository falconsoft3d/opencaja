import shutil
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app.decorators import admin_required
from app.extensions import db

bp = Blueprint("respaldo", __name__, url_prefix="/respaldos")

SQLITE_HEADER = b"SQLite format 3\x00"


def _ruta_db():
    """Ruta local del archivo SQLite, o None si se usa otro motor de base de datos."""
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        return None
    resto = uri[len("sqlite:///") :]
    path = f"/{resto}" if uri.startswith("sqlite:////") else resto
    return Path(path)


@bp.route("/")
@login_required
@admin_required
def index():
    ruta = _ruta_db()
    info = None
    if ruta and ruta.exists():
        stat = ruta.stat()
        info = {
            "size_mb": stat.st_size / (1024 * 1024),
            "modificado": datetime.fromtimestamp(stat.st_mtime),
        }
    return render_template("respaldo.html", info=info, es_sqlite=ruta is not None)


@bp.route("/descargar")
@login_required
@admin_required
def descargar():
    ruta = _ruta_db()
    if not ruta or not ruta.exists():
        flash("No se encontró la base de datos para respaldar.", "danger")
        return redirect(url_for("respaldo.index"))
    db.session.commit()
    nombre = f"opencaja_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    return send_file(ruta, as_attachment=True, download_name=nombre)


@bp.route("/restaurar", methods=["POST"])
@login_required
@admin_required
def restaurar():
    ruta = _ruta_db()
    if not ruta:
        flash("Restaurar solo está disponible cuando se usa SQLite.", "danger")
        return redirect(url_for("respaldo.index"))

    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        flash("Selecciona un archivo de respaldo (.db) para restaurar.", "danger")
        return redirect(url_for("respaldo.index"))

    cabecera = archivo.stream.read(len(SQLITE_HEADER))
    archivo.stream.seek(0)
    if cabecera != SQLITE_HEADER:
        flash("El archivo no parece ser una base de datos SQLite válida.", "danger")
        return redirect(url_for("respaldo.index"))

    db.session.remove()
    db.engine.dispose()

    if ruta.exists():
        copia_seguridad = ruta.with_name(f"pre_restauracion_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(ruta, copia_seguridad)

    archivo.save(str(ruta))

    flash(
        "Base de datos restaurada correctamente. Se guardó una copia de la base anterior por "
        "seguridad. Reinicia la aplicación para que todo funcione con los datos restaurados "
        "(es posible que tu sesión se cierre si el usuario no existe en la base restaurada).",
        "success",
    )
    return redirect(url_for("respaldo.index"))
