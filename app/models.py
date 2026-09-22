from datetime import date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    pin_hash = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        if not self.pin_hash or not pin:
            return False
        return check_password_hash(self.pin_hash, pin)

    @property
    def has_pin(self):
        return self.pin_hash is not None

    def __repr__(self):
        return f"<User {self.username}>"


class Proyecto(db.Model):
    __tablename__ = "proyectos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    importe_cobrar = db.Column(db.Numeric(12, 2), nullable=False, default=0)


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(30), nullable=False)


class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(30), nullable=False)


class IntegracionConfig(db.Model):
    __tablename__ = "integracion_config"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=True)

    @classmethod
    def obtener(cls):
        config = cls.query.get(1)
        if not config:
            config = cls(id=1, url=None)
            db.session.add(config)
            db.session.commit()
        return config


class Diario(db.Model):
    __tablename__ = "diarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)


class PagoCliente(db.Model):
    __tablename__ = "pagos_cliente"

    id = db.Column(db.Integer, primary_key=True)
    secuencia = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    importe = db.Column(db.Numeric(12, 2), nullable=False)
    diario_id = db.Column(db.Integer, db.ForeignKey("diarios.id"), nullable=False)
    moneda = db.Column(db.String(10), nullable=False, default="EUR")
    nota = db.Column(db.Text, nullable=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyectos.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)

    proyecto = db.relationship("Proyecto")
    cliente = db.relationship("Cliente")
    diario = db.relationship("Diario")


class PagoProveedor(db.Model):
    __tablename__ = "pagos_proveedor"

    id = db.Column(db.Integer, primary_key=True)
    secuencia = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    importe = db.Column(db.Numeric(12, 2), nullable=False)
    diario_id = db.Column(db.Integer, db.ForeignKey("diarios.id"), nullable=False)
    moneda = db.Column(db.String(10), nullable=False, default="EUR")
    nota = db.Column(db.Text, nullable=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyectos.id"), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"), nullable=False)

    proyecto = db.relationship("Proyecto")
    proveedor = db.relationship("Proveedor")
    diario = db.relationship("Diario")
