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
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

MONEDAS = [("EUR", "EUR"), ("USD", "USD"), ("RUB", "RUB"), ("BTC", "BTC")]


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Ingresar")


class ProyectoForm(FlaskForm):
    codigo = StringField("Código", validators=[DataRequired(), Length(max=40)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    importe_cobrar = DecimalField("Importe a cobrar", validators=[DataRequired()], places=2)
    submit = SubmitField("Guardar")


class ClienteForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    telefono = StringField("Teléfono", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Guardar")


class ProveedorForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    telefono = StringField("Teléfono", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Guardar")


class PagoClienteForm(FlaskForm):
    proyecto_id = SelectField("Proyecto", coerce=int, validators=[DataRequired()])
    cliente_id = SelectField("Cliente", coerce=int, validators=[DataRequired()])
    fecha = DateField("Fecha", validators=[DataRequired()])
    importe = DecimalField("Importe", validators=[DataRequired()], places=2)
    moneda = SelectField("Moneda", choices=MONEDAS, default="EUR", validators=[DataRequired()])
    nota = TextAreaField("Nota", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Guardar")


class PagoProveedorForm(FlaskForm):
    proyecto_id = SelectField("Proyecto", coerce=int, validators=[DataRequired()])
    proveedor_id = SelectField("Proveedor", coerce=int, validators=[DataRequired()])
    fecha = DateField("Fecha", validators=[DataRequired()])
    importe = DecimalField("Importe", validators=[DataRequired()], places=2)
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
