from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import PerfilForm
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
    return render_template("perfil.html", form=form)
