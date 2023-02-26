from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, PasswordField
from wtforms.validators import Regexp, Length, InputRequired


class AddRecordUser(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    nome = StringField('Name', [ InputRequired(),
        Regexp(r'^[A-Za-z\s\-\']+$', message="Invalid name"),
        Length(min=3, max=25, message="Invalid name length")
        ])
    cognome = StringField('Surname', [ InputRequired(),
                          Regexp(r'^[A-Za-z\s\-\']+$', message="Invalid surname"),
                          Length(min=3, max=25, message="Invalid surname length")
    ])
    email = StringField('Email', [ InputRequired(),
                          Length(min=3, max=25, message="Invalid email length")
    ])
    indirizzo = StringField('Address', [InputRequired(),
                                    Regexp(r'^[A-Za-z\s\-\']+$', message="Invalid address"),
                                    Length(min=3, max=25, message="Invalid address length")
                                    ])
    telefono = StringField('Phone', [InputRequired(),
                                          Regexp(r'^[1-9\s\-\']+$', message="Invalid phone"),
                                          Length(min=3, max=25, message="Invalid phone length")
                                          ])
    password = PasswordField('Password', [InputRequired(),
                                        Regexp(r'^[A-Za-z\s\-\']+$', message="Invalid password"),
                                        Length(min=3, max=25, message="Invalid password length")
                                        ])

    # updated - date - handled in the route function
    updated = HiddenField()
    submit = SubmitField('Submit')






