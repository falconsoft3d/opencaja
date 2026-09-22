from decimal import Decimal, InvalidOperation

import requests
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app.decorators import admin_required
from app.extensions import db
from app.forms import IntegracionForm
from app.models import IntegracionConfig, Proyecto

bp = Blueprint("integracion", __name__, url_prefix="/integracion")


def _a_decimal(valor):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _importar_proyectos(url):
    """Descarga el JSON de proyectos: crea los que falten (name -> codigo, nombre ->
    nombre, discount -> importe a cobrar) y actualiza el importe a cobrar de los que
    ya existen.

    Devuelve (creados, actualizados, omitidos).
    """
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("La respuesta no es una lista de proyectos.")

    existentes = {p.codigo: p for p in Proyecto.query.all()}
    creados = 0
    actualizados = 0
    omitidos = 0
    for item in data:
        if not isinstance(item, dict):
            omitidos += 1
            continue
        codigo = str(item.get("name") or "").strip()
        if not codigo:
            omitidos += 1
            continue
        importe_cobrar = _a_decimal(item.get("discount"))

        proyecto = existentes.get(codigo)
        if proyecto is not None:
            if proyecto.importe_cobrar != importe_cobrar:
                proyecto.importe_cobrar = importe_cobrar
                actualizados += 1
            else:
                omitidos += 1
            continue

        nombre = str(item.get("nombre") or "").strip() or codigo
        nuevo = Proyecto(codigo=codigo, nombre=nombre, importe_cobrar=importe_cobrar)
        db.session.add(nuevo)
        existentes[codigo] = nuevo
        creados += 1

    db.session.commit()
    return creados, actualizados, omitidos


@bp.route("/", methods=["GET", "POST"])
@login_required
@admin_required
def index():
    config = IntegracionConfig.obtener()
    form = IntegracionForm(obj=config)
    if form.validate_on_submit():
        config.url = form.url.data
        db.session.commit()
        flash("URL de integración guardada.", "success")
        return redirect(url_for("integracion.index"))
    return render_template("integracion.html", form=form, config=config)


@bp.route("/importar", methods=["POST"])
@login_required
@admin_required
def importar():
    config = IntegracionConfig.obtener()
    if not config.url:
        flash("Primero configura la URL del servicio.", "danger")
        return redirect(url_for("integracion.index"))
    try:
        creados, actualizados, omitidos = _importar_proyectos(config.url)
        flash(
            f"Importación completa: {creados} creado(s), {actualizados} actualizado(s) "
            f"(importe a cobrar), {omitidos} sin cambios.",
            "success",
        )
    except requests.exceptions.RequestException as exc:
        flash(f"No se pudo contactar la URL configurada: {exc}", "danger")
    except ValueError as exc:
        flash(f"Respuesta inválida del servicio: {exc}", "danger")
    return redirect(url_for("integracion.index"))
