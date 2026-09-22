from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import PerfilForm, PinForm
from app.models import Cliente, PagoCliente, PagoProveedor, Proyecto

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        total_proyectos=Proyecto.query.count(),
        total_clientes=Cliente.query.count(),
        total_pagos_cliente=PagoCliente.query.count(),
        total_pagos_proveedor=PagoProveedor.query.count(),
    )


@bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    form = PerfilForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("La contraseña actual no es correcta.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("main.perfil"))
    return render_template("perfil.html", form=form, pin_form=PinForm())


@bp.route("/perfil/pin", methods=["POST"])
@login_required
def actualizar_pin():
    pin_form = PinForm()
    if pin_form.validate_on_submit():
        current_user.set_pin(pin_form.pin.data)
        db.session.commit()
        flash("PIN guardado correctamente.", "success")
    else:
        flash("El PIN debe tener entre 4 y 6 dígitos e ingresarse igual en ambos campos.", "danger")
    return redirect(url_for("main.perfil"))


@bp.route("/perfil/pin/eliminar", methods=["POST"])
@login_required
def eliminar_pin():
    current_user.pin_hash = None
    db.session.commit()
    flash("PIN eliminado. Ahora la sesión se cerrará tras 5 minutos de inactividad.", "info")
    return redirect(url_for("main.perfil"))


@bp.route("/verificar-pin", methods=["POST"])
@login_required
def verificar_pin():
    data = request.get_json(silent=True) or {}
    return jsonify({"ok": current_user.check_pin(data.get("pin", ""))})
