import click
from flask import Flask, render_template, url_for
from flask_login import login_required
from sqlalchemy import func

from app.decorators import admin_required
from app.extensions import csrf, db, login_manager
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import bp as auth_bp
    from app.integracion import bp as integracion_bp
    from app.main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(integracion_bp)

    for crud_bp in build_crud_blueprints():
        app.register_blueprint(crud_bp)

    register_cli(app)

    return app


def next_secuencia(model, prefix):
    """Calcula el siguiente número de secuencia (ej. PE/00001) a partir del mayor existente."""
    max_num = 0
    with db.session.no_autoflush:
        rows = model.query.with_entities(model.secuencia).all()
    for (secuencia,) in rows:
        if secuencia and secuencia.startswith(f"{prefix}/"):
            try:
                max_num = max(max_num, int(secuencia.split("/", 1)[1]))
            except ValueError:
                continue
    return f"{prefix}/{max_num + 1:05d}"


def nombre_o_referencia(entidad, prefijo):
    """Nombre para mostrar de un Cliente/Proveedor cuyo nombre es opcional."""
    return entidad.nombre or entidad.email or f"{prefijo} #{entidad.id}"


def restar_por_moneda(cobrado, pagado):
    """Combina dos listas [(moneda, monto), ...] restando pagado a cobrado por moneda."""
    cobros = dict(cobrado)
    pagos = dict(pagado)
    monedas = sorted(set(cobros) | set(pagos))
    return [(m, (cobros.get(m) or 0) - (pagos.get(m) or 0)) for m in monedas]


def saldo_por_moneda(diario_id=None):
    """Cobrado (Pagos de Cliente) menos pagado (Pagos a Proveedor), agrupado por moneda.

    Sin diario_id, calcula el total sobre todos los diarios.
    """
    from app.models import PagoCliente, PagoProveedor

    cobros_query = db.session.query(PagoCliente.moneda, func.sum(PagoCliente.importe))
    pagos_query = db.session.query(PagoProveedor.moneda, func.sum(PagoProveedor.importe))
    if diario_id is not None:
        cobros_query = cobros_query.filter(PagoCliente.diario_id == diario_id)
        pagos_query = pagos_query.filter(PagoProveedor.diario_id == diario_id)
    cobros = cobros_query.group_by(PagoCliente.moneda).all()
    pagos = pagos_query.group_by(PagoProveedor.moneda).all()
    return restar_por_moneda(cobros, pagos)


def formatear_saldos(saldos):
    if not saldos:
        return "0.00 EUR"
    return ", ".join(f"{monto:.2f} {moneda}" for moneda, monto in saldos)


def register_diario_detalle_route(diarios_bp):
    from app.models import Diario, PagoCliente, PagoProveedor

    def _totales_por_moneda(model, diario_id):
        return (
            db.session.query(model.moneda, func.sum(model.importe))
            .filter(model.diario_id == diario_id)
            .group_by(model.moneda)
            .all()
        )

    @diarios_bp.route("/<int:item_id>")
    @login_required
    def detalle(item_id):
        diario = Diario.query.get_or_404(item_id)
        pagos_cliente = PagoCliente.query.filter_by(diario_id=item_id).order_by(PagoCliente.id.desc()).all()
        pagos_proveedor = (
            PagoProveedor.query.filter_by(diario_id=item_id).order_by(PagoProveedor.id.desc()).all()
        )
        return render_template(
            "diario_detalle.html",
            diario=diario,
            cobrado_por_moneda=_totales_por_moneda(PagoCliente, item_id),
            pagado_por_moneda=_totales_por_moneda(PagoProveedor, item_id),
            saldo_por_moneda=saldo_por_moneda(diario_id=item_id),
            pagos_cliente=pagos_cliente,
            pagos_proveedor=pagos_proveedor,
        )


def build_crud_blueprints():
    from app.crud import CrudValidationError, make_crud_blueprint
    from app.forms import (
        ClienteForm,
        DiarioForm,
        PagoClienteForm,
        PagoProveedorForm,
        ProveedorForm,
        ProyectoForm,
        UsuarioForm,
    )
    from app.models import Cliente, Diario, PagoCliente, PagoProveedor, Proveedor, Proyecto, User

    proyectos_bp = make_crud_blueprint(
        name="proyectos",
        import_name=__name__,
        model=Proyecto,
        form_class=ProyectoForm,
        columns=[("codigo", "Código"), ("nombre", "Nombre"), ("importe_cobrar", "Importe a cobrar")],
        title="Proyectos",
        singular="Proyecto",
        extra_row_action={"endpoint": "detalle", "label": "Ver", "icon": "bi-eye"},
    )
    register_proyecto_detalle_route(proyectos_bp)

    clientes_bp = make_crud_blueprint(
        name="clientes",
        import_name=__name__,
        model=Cliente,
        form_class=ClienteForm,
        columns=[("nombre", "Nombre"), ("email", "Email"), ("telefono", "Teléfono")],
        title="Clientes",
        singular="Cliente",
    )

    proveedores_bp = make_crud_blueprint(
        name="proveedores",
        import_name=__name__,
        model=Proveedor,
        form_class=ProveedorForm,
        columns=[("nombre", "Nombre"), ("email", "Email"), ("telefono", "Teléfono")],
        title="Proveedores",
        singular="Proveedor",
    )

    def diario_saldo_columna(diario):
        return formatear_saldos(saldo_por_moneda(diario_id=diario.id))

    def diarios_footer(_items):
        return ["Total", formatear_saldos(saldo_por_moneda())]

    diarios_bp = make_crud_blueprint(
        name="diarios",
        import_name=__name__,
        model=Diario,
        form_class=DiarioForm,
        columns=[("nombre", "Nombre"), (diario_saldo_columna, "Saldo (cobrado - pagado)")],
        title="Diarios",
        singular="Diario",
        extra_row_action={"endpoint": "detalle", "label": "Ver", "icon": "bi-eye"},
        footer=diarios_footer,
    )
    register_diario_detalle_route(diarios_bp)

    def pago_cliente_form_init(form):
        form.proyecto_id.choices = [
            (p.id, f"{p.codigo} - {p.nombre}") for p in Proyecto.query.order_by(Proyecto.nombre).all()
        ]
        form.cliente_id.choices = [
            (c.id, c.nombre or c.email or f"Cliente #{c.id}")
            for c in Cliente.query.order_by(Cliente.nombre).all()
        ]
        form.diario_id.choices = [(d.id, d.nombre) for d in Diario.query.order_by(Diario.nombre).all()]

    def pago_cliente_before_save(instance, form, is_create):
        if is_create:
            instance.secuencia = next_secuencia(PagoCliente, "PE")

    pagos_cliente_bp = make_crud_blueprint(
        name="pagos_cliente",
        import_name=__name__,
        model=PagoCliente,
        form_class=PagoClienteForm,
        columns=[
            ("secuencia", "Secuencia"),
            ("proyecto.codigo", "Proyecto"),
            (lambda p: nombre_o_referencia(p.cliente, "Cliente"), "Cliente"),
            ("fecha", "Fecha"),
            ("importe", "Importe"),
            ("diario.nombre", "Diario"),
            ("moneda", "Moneda"),
        ],
        title="Pagos de Cliente",
        singular="Pago de Cliente",
        before_save=pago_cliente_before_save,
        form_init=pago_cliente_form_init,
        extra_row_action={"endpoint": "comprobante", "label": "Comprobante", "icon": "bi-printer"},
    )

    def pago_proveedor_form_init(form):
        form.proyecto_id.choices = [
            (p.id, f"{p.codigo} - {p.nombre}") for p in Proyecto.query.order_by(Proyecto.nombre).all()
        ]
        form.proveedor_id.choices = [
            (pv.id, pv.nombre or pv.email or f"Proveedor #{pv.id}")
            for pv in Proveedor.query.order_by(Proveedor.nombre).all()
        ]
        form.diario_id.choices = [(d.id, d.nombre) for d in Diario.query.order_by(Diario.nombre).all()]

    def pago_proveedor_before_save(instance, form, is_create):
        if is_create:
            instance.secuencia = next_secuencia(PagoProveedor, "PS")

    pagos_proveedor_bp = make_crud_blueprint(
        name="pagos_proveedor",
        import_name=__name__,
        model=PagoProveedor,
        form_class=PagoProveedorForm,
        columns=[
            ("secuencia", "Secuencia"),
            ("proyecto.codigo", "Proyecto"),
            (lambda p: nombre_o_referencia(p.proveedor, "Proveedor"), "Proveedor"),
            ("fecha", "Fecha"),
            ("importe", "Importe"),
            ("diario.nombre", "Diario"),
            ("moneda", "Moneda"),
        ],
        title="Pagos a Proveedor",
        singular="Pago a Proveedor",
        before_save=pago_proveedor_before_save,
        form_init=pago_proveedor_form_init,
        extra_row_action={"endpoint": "comprobante", "label": "Comprobante", "icon": "bi-printer"},
    )

    register_comprobante_routes(pagos_cliente_bp, pagos_proveedor_bp)

    def usuario_before_save(instance, form, is_create):
        if is_create and not form.password.data:
            raise CrudValidationError("La contraseña es obligatoria al crear un usuario.")
        if form.password.data:
            instance.set_password(form.password.data)

    usuarios_bp = make_crud_blueprint(
        name="usuarios",
        import_name=__name__,
        model=User,
        form_class=UsuarioForm,
        columns=[("username", "Usuario"), ("email", "Email"), ("is_admin", "Administrador")],
        title="Usuarios",
        singular="Usuario",
        before_save=usuario_before_save,
        exclude_fields=["password"],
        extra_decorators=[admin_required],
    )

    return [
        proyectos_bp,
        clientes_bp,
        proveedores_bp,
        diarios_bp,
        pagos_cliente_bp,
        pagos_proveedor_bp,
        usuarios_bp,
    ]


def register_comprobante_routes(pagos_cliente_bp, pagos_proveedor_bp):
    from app.models import PagoCliente, PagoProveedor

    @pagos_cliente_bp.route("/<int:item_id>/comprobante")
    @login_required
    def comprobante(item_id):
        pago = PagoCliente.query.get_or_404(item_id)
        return render_template(
            "comprobante.html",
            pago=pago,
            tipo="Pago de Cliente",
            tercero_label="Cliente",
            tercero_nombre=nombre_o_referencia(pago.cliente, "Cliente"),
            back_url=url_for("pagos_cliente.index"),
        )

    @pagos_proveedor_bp.route("/<int:item_id>/comprobante")
    @login_required
    def comprobante(item_id):  # noqa: F811 - registrado en un blueprint distinto
        pago = PagoProveedor.query.get_or_404(item_id)
        return render_template(
            "comprobante.html",
            pago=pago,
            tipo="Pago a Proveedor",
            tercero_label="Proveedor",
            tercero_nombre=nombre_o_referencia(pago.proveedor, "Proveedor"),
            back_url=url_for("pagos_proveedor.index"),
        )


def register_proyecto_detalle_route(proyectos_bp):
    from app.models import PagoCliente, PagoProveedor, Proyecto

    def _totales_por_moneda(model, proyecto_id):
        return (
            db.session.query(model.moneda, func.sum(model.importe))
            .filter(model.proyecto_id == proyecto_id)
            .group_by(model.moneda)
            .all()
        )

    @proyectos_bp.route("/<int:item_id>")
    @login_required
    def detalle(item_id):
        proyecto = Proyecto.query.get_or_404(item_id)
        pagos_cliente = PagoCliente.query.filter_by(proyecto_id=item_id).order_by(PagoCliente.id.desc()).all()
        pagos_proveedor = (
            PagoProveedor.query.filter_by(proyecto_id=item_id).order_by(PagoProveedor.id.desc()).all()
        )
        cobrado_por_moneda = _totales_por_moneda(PagoCliente, item_id)
        pagado_por_moneda = _totales_por_moneda(PagoProveedor, item_id)
        return render_template(
            "proyecto_detalle.html",
            proyecto=proyecto,
            cobrado_por_moneda=cobrado_por_moneda,
            pagado_por_moneda=pagado_por_moneda,
            saldo_por_moneda=restar_por_moneda(cobrado_por_moneda, pagado_por_moneda),
            pagos_cliente=pagos_cliente,
            pagos_proveedor=pagos_proveedor,
        )


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas de la base de datos."""
        db.create_all()
        click.echo("Base de datos inicializada.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, password):
        """Crea un usuario administrador."""
        from app.models import User

        if User.query.filter_by(username=username).first():
            click.echo("Ese usuario ya existe.")
            return
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Usuario admin '{username}' creado correctamente.")
