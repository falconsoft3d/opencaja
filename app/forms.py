from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, Length, Optional, Regexp

MONEDAS = [("EUR", "EUR"), ("USD", "USD"), ("RUB", "RUB"), ("BTC", "BTC")]


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Ingresar")


class ProyectoForm(FlaskForm):
    codigo = StringField("Código", validators=[DataRequired(), Length(max=40)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    importe_cobrar = DecimalField("Importe a cobrar", validators=[InputRequired()], places=2)
    submit = SubmitField("Guardar")


class ClienteForm(FlaskForm):
    nombre = StringField("Nombre", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    telefono = StringField("Teléfono", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Guardar")


class ProveedorForm(FlaskForm):
    nombre = StringField("Nombre", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    telefono = StringField("Teléfono", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Guardar")


class DiarioForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Guardar")


class PagoClienteForm(FlaskForm):
    proyecto_id = SelectField("Proyecto", coerce=int, validators=[DataRequired()])
    cliente_id = SelectField("Cliente", coerce=int, validators=[DataRequired()])
    fecha = DateField("Fecha", validators=[DataRequired()])
    importe = DecimalField("Importe", validators=[InputRequired()], places=2)
    diario_id = SelectField("Diario", coerce=int, validators=[DataRequired()])
    moneda = SelectField("Moneda", choices=MONEDAS, default="EUR", validators=[DataRequired()])
    nota = TextAreaField("Nota", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Guardar")


class PagoProveedorForm(FlaskForm):
    proyecto_id = SelectField("Proyecto", coerce=int, validators=[DataRequired()])
    proveedor_id = SelectField("Proveedor", coerce=int, validators=[DataRequired()])
    fecha = DateField("Fecha", validators=[DataRequired()])
    importe = DecimalField("Importe", validators=[InputRequired()], places=2)
    diario_id = SelectField("Diario", coerce=int, validators=[DataRequired()])
    moneda = SelectField("Moneda", choices=MONEDAS, default="EUR", validators=[DataRequired()])
    nota = TextAreaField("Nota", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Guardar")


class UsuarioForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Contraseña", validators=[Optional(), Length(min=6, message="Mínimo 6 caracteres")]
    )
    is_admin = BooleanField("Administrador")
    submit = SubmitField("Guardar")


class PerfilForm(FlaskForm):
    current_password = PasswordField("Contraseña actual", validators=[DataRequired()])
    new_password = PasswordField("Nueva contraseña", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[DataRequired(), EqualTo("new_password", message="Las contraseñas no coinciden")],
    )
    submit = SubmitField("Cambiar contraseña")


class PinForm(FlaskForm):
    pin = PasswordField(
        "PIN (4 a 6 dígitos)",
        validators=[
            DataRequired(),
            Length(min=4, max=6),
            Regexp(r"^\d+$", message="El PIN solo puede contener dígitos"),
        ],
    )
    confirmar_pin = PasswordField(
        "Confirmar PIN",
        validators=[DataRequired(), EqualTo("pin", message="Los PIN no coinciden")],
    )
    submit_pin = SubmitField("Guardar PIN")


class IntegracionForm(FlaskForm):
    url = StringField(
        "URL del servicio",
        validators=[DataRequired(), Length(max=500)],
        render_kw={"placeholder": "http://167.233.206.103:8069/bim_report_sql/KS0HW443E8"},
    )
    submit = SubmitField("Guardar URL")
