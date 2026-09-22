from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db


class CrudValidationError(Exception):
    """Se lanza desde un hook before_save para rechazar el guardado con un mensaje propio."""


def _resolve(item, attr):
    value = item
    for part in attr.split("."):
        value = getattr(value, part)
    return value


def make_crud_blueprint(
    name,
    import_name,
    model,
    form_class,
    columns,
    title,
    singular,
    before_save=None,
    exclude_fields=None,
    extra_decorators=None,
    form_init=None,
    extra_row_action=None,
):
    """Crea un blueprint con las vistas listar/crear/editar/eliminar para un modelo.

    columns: lista de (atributo, etiqueta) mostrados en la tabla del listado; el atributo
        admite notación con puntos para relaciones (ej. "proyecto.nombre").
    before_save: callback(instance, form, is_create) para lógica extra (ej. hash de password,
        generar una secuencia autoincremental).
    exclude_fields: campos del formulario que no deben copiarse directo al modelo.
    form_init: callback(form) llamado tras instanciar el formulario, para poblar choices
        dinámicos (ej. SelectField de un modelo relacionado) antes de validar/renderizar.
    extra_row_action: dict {"endpoint", "label", "icon"} para un botón extra por fila en el
        listado, que enlaza a url_for(f"{name}.{endpoint}", item_id=...) (ej. comprobante).
    """
    bp = Blueprint(name, import_name, url_prefix=f"/{name}")
    decorators = [login_required] + (extra_decorators or [])
    exclude_fields = set(exclude_fields or []) | {"csrf_token", "submit"}

    def apply_decorators(view):
        for decorator in reversed(decorators):
            view = decorator(view)
        return view

    def _populate(instance, form):
        for field_name, field in form._fields.items():
            if field_name in exclude_fields:
                continue
            setattr(instance, field_name, field.data)

    def _save(instance, form, is_create):
        _populate(instance, form)
        try:
            if before_save:
                before_save(instance, form, is_create)
        except CrudValidationError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return False
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            flash("Ya existe un registro con esos datos (valor duplicado).", "danger")
            return False

    def index():
        items = model.query.order_by(model.id.desc()).all()
        rows = [{"instance": item, "cells": [_resolve(item, attr) for attr, _ in columns]} for item in items]
        return render_template(
            "crud/list.html",
            rows=rows,
            columns=columns,
            title=title,
            singular=singular,
            endpoint=name,
            extra_row_action=extra_row_action,
        )

    def create():
        form = form_class()
        if form_init:
            form_init(form)
        if form.validate_on_submit():
            instance = model()
            db.session.add(instance)
            if _save(instance, form, True):
                flash(f"{singular} creado correctamente.", "success")
                return redirect(url_for(f"{name}.index"))
        return render_template("crud/form.html", form=form, title=f"Nuevo {singular}", endpoint=name)

    def edit(item_id):
        instance = model.query.get_or_404(item_id)
        form = form_class(obj=instance)
        if form_init:
            form_init(form)
        if form.validate_on_submit():
            if _save(instance, form, False):
                flash(f"{singular} actualizado correctamente.", "success")
                return redirect(url_for(f"{name}.index"))
        return render_template(
            "crud/form.html", form=form, title=f"Editar {singular}", endpoint=name, instance=instance
        )

    def delete(item_id):
        instance = model.query.get_or_404(item_id)
        db.session.delete(instance)
        db.session.commit()
        flash(f"{singular} eliminado.", "info")
        return redirect(url_for(f"{name}.index"))

    bp.add_url_rule("/", view_func=apply_decorators(index), endpoint="index")
    bp.add_url_rule("/nuevo", view_func=apply_decorators(create), endpoint="create", methods=["GET", "POST"])
    bp.add_url_rule(
        "/<int:item_id>/editar", view_func=apply_decorators(edit), endpoint="edit", methods=["GET", "POST"]
    )
    bp.add_url_rule(
        "/<int:item_id>/eliminar", view_func=apply_decorators(delete), endpoint="delete", methods=["POST"]
    )

    return bp
