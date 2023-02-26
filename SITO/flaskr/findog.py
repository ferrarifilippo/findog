"""
    test a SQLite database connection locally
    assumes database file is in same location
    as this .py file
"""
import datetime
import hashlib
import math
import re

from flask_migrate import Migrate
from sqlalchemy.sql import text
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user, LoginManager, login_user, login_required, logout_user
from flask_bootstrap import Bootstrap

from SITO.flaskr.models import db, Dog, DogOwner, Walk, Habits
from SITO.flaskr.forms import AddRecordUser
from SITO.flaskr.telegram_bot import dog_found, walk_handler_v3
from SITO.flaskr.utils import check_habits, set_day_slot

app = Flask(__name__)

# change to name of your database; add path if necessary
db_name = 'findog.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'MLXH243GssUWwKdTWS7FDhdwYF56wPj8'

# Flask-Bootstrap requires this line
Bootstrap(app)

migrate = Migrate(app, db)

# this variable, db, will be used for all SQLAlchemy commands
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
debug = True
@app.route('/debug', methods=['GET'])
def debug():
    global debug
    debug = request.args.get('debug')
    if debug == 1:
        debug = False
    elif debug == 0:
        debug = True

@login_manager.user_loader
def load_user(user_id):
    return DogOwner.query.get(user_id)


# NOTHING BELOW THIS LINE NEEDS TO CHANGE
# this route will test the database connection and nothing more
@app.route('/')
def testdb():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return render_template('index.html')
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form1 = AddRecordUser()
    if request.method == 'POST':
        nome = request.form.get('name')
        cognome = request.form.get('surname')
        email = request.form.get('email')
        indirizzo = request.form.get('address')
        telefono = request.form.get('numb')
        passw = request.form.get('psw')
        user = DogOwner.query.filter_by(email=email).first()
        if user:
            flash("Email address already exist")
            return render_template('signup.html')
        elif email == "" or passw == "":
            flash('Password e email non possono essere vuoti')
            return render_template('signup.html')
        # the data to be inserted into Sock model - the table, socks
        passw = hashlib.sha256(passw.encode()).hexdigest()
        record = DogOwner(first_name=nome, last_name=cognome, email=email, address=indirizzo, phone=telefono,
                          password=passw
                          # ,dog=[Dog()]
                          )
        # Flask-SQLAlchemy magic adds record to database
        db.session.add(record)
        db.session.commit()
        login_user(record, remember=True)
        # create a message to send to the template
        message = f"The data for owner {nome} has been submitted."
        # return render_template('login.html')

        return redirect(url_for("profile", usr=nome))
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')

        return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('psw')
        password = hashlib.sha256(password.encode()).hexdigest()
        user = DogOwner.query.filter_by(email=email, password=password).first()

        if not user:
            flash('La mail non esiste, vuoi registrarti ?')
            return render_template('login.html')
        elif not user.password == password:
            flash('Password invalida')
            return render_template('login.html')
        elif email == "" or password == "":
            flash('Password e email non possono essere vuoti')
            return render_template('login.html')
        else:
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for("profile", usr=user.id))

    else:
        return render_template("login.html")


@app.route("/bridge_login", methods=["GET"])
def bridge_login():
    email = request.args.get('email')
    password = request.args.get('password')
    user = DogOwner.query.filter_by(email=email, password=password).first()
    if user:
        return str(user.id)
    else:
        return "auth_error"


@app.route("/telegram_login", methods=["POST"])
def telegram_login():
    email = request.form.get('email')
    password = request.form.get('password')
    chat_id = request.form.get('chat_id')
    user = DogOwner.query.filter_by(email=email, password=password).first()
    if user:
        user.telegram_chat_id = chat_id
        db.session.add(user)
        db.session.commit()
        return str(user.first_name)
    else:
        return "auth_error"


@app.route("/bridge_name_to_uuid", methods=["GET"])
def bridge_name_to_uuid():
    user = request.args.get('user')
    dog_name = request.args.get('dog_name')
    dog = Dog.query.filter_by(name=dog_name, user=int(user)).first()
    if dog:
        return dog.uuid
    else:
        return "dog_error"


@app.route("/dog_is_paired", methods=["GET"])
def get_dog_is_paired():
    uuid = request.args.get('uuid')
    dog = Dog.query.filter_by(uuid=uuid).first()
    dog.bridge_paired = False
    return not dog.bridge_paired


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return render_template("logout.html")


@app.route('/new_dog', methods=['GET', 'POST'])
@login_required
def new_dog():
    form1 = AddRecordUser()
    if request.method == 'POST':
        uuid = "{0:0>4}"
        try:
            id = int(re.findall(r'\d+', ((Dog.query.order_by(Dog.created_at.desc())).first()).uuid)[0])
            id += 1
        except:
            id = 1
        uuid = uuid.format(id)
        # print("test")
        # print(f"UUID == {uuid}")  # instead of print you should do whatever you ne
        nome = request.form.get('name')
        colore = request.form.get('color')
        razza = request.form.get('breed')

        # the data to be inserted into Sock model - the table, socks
        # Set dello stato del cana ad A = "in casa"
        dogowner = DogOwner.query.filter_by(id=current_user.get_id()).first()
        if nome == "" or razza == "":
            flash('Nome e razza non possono essere vuoti')
            return render_template('newdog.html')
        else:
            record = Dog(uuid=uuid, name=nome.lower(), color=colore, breed=razza, user=dogowner.id, state='A'
                         )
            # Flask-SQLAlchemy magic adds record to database
            db.session.add(record)
            db.session.commit()
        # create a message to send to the template
        # message = f"The data for owner {nome} has been submitted."
        # return render_template('login.html')

        return redirect(url_for("profile", usr=dogowner.id))
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')

        return render_template("newdog.html")


@app.route('/doglist')
def dog_list():
    return render_template('doglist.html', object_list=Dog.query.filter_by(user=current_user.get_id()))


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/profile")
@login_required
def profile():
    dog_owner = DogOwner.query.filter_by(id=current_user.get_id()).first()
    return render_template("profile.html", user=dog_owner)


@app.route("/set_dog", methods=['POST'])
def set_dog():
    uuid = request.form.get('uuid')
    attribute = request.form.get('attribute')
    dog = Dog.query.filter_by(uuid=uuid).first_or_404()
    val = request.form.get('val')
    setattr(dog, attribute, val)
    db.session.add(dog)
    db.session.commit()
    return Response(status=204)


@app.route("/get_dog", methods=['GET'])
def get_dog():
    uuid = request.args.get('uuid')
    attribute = request.args.get('attribute')
    dog = Dog.query.filter_by(uuid=uuid).first_or_404()
    return str(getattr(dog, attribute))


@app.route("/get_user", methods=['GET'])
def get_user():
    uuid = request.args.get('uuid')
    message_chat_id = request.args.get('chat_id')
    dog = Dog.query.filter_by(uuid=uuid).first()
    if dog is not None:
        user = DogOwner.query.filter_by(id=dog.user).first()

        db.session.add(user)
        db.session.commit()
        return user.first_name
    else:
        return "Nessun Risultato"


@app.route("/get_dog_uuid", methods=['GET'])
def get_dog_uuid():
    message_chat_id = request.args.get('chat_id')
    user = DogOwner.query.filter_by(telegram_chat_id=message_chat_id).first()
    dog = user.dog.filter_by(state='W').first()
    return dog.uuid


@app.route("/walk_telegram", methods=['GET'])
def walk_telegram():
    uuid = request.args.get('uuid')
    dog = Dog.query.filter_by(uuid=uuid).first()
    user = DogOwner.query.filter_by(id=dog.user).first()
    global debug
    if not check_habits(uuid) or debug:
        walk_handler_v3(user.telegram_chat_id, uuid)
    else:
        dog.state = "P"
        new_walk(uuid)

    db.session.commit()

    return user.telegram_chat_id


@app.route("/dog_found_telegram", methods=['GET'])
def dog_found_telegram():
    address_uuid = request.args.get('my_uuid')
    other_uuid = request.args.get('other_uuid')
    dog = Dog.query.filter_by(uuid=address_uuid).first()
    dog_ex = Dog.query.filter_by(uuid=other_uuid).first()
    user = DogOwner.query.filter_by(id=dog.user).first()
    user_found = DogOwner.query.filter_by(id=dog_ex.user).first()
    dog_found(user.address, user_found.telegram_chat_id)

    return user.telegram_chat_id


@app.route("/new_walk", methods=['POST'])
def new_walk(dog_uuid=None):
    if dog_uuid is None:
        dog_uuid = request.form.get('uuid')
    time = datetime.datetime.now()
    day_slot = set_day_slot(time)
    if day_slot:
        walk = Walk(dog=dog_uuid, time=time, day_slot=day_slot)
    else:
        return Response(status=500)
    db.session.add(walk)
    db.session.commit()

    mean_time = 0
    mean_hour = 0
    # mean_minute = 0
    walks = Walk.query.filter_by(dog=dog_uuid, day_slot=day_slot).all()
    number_walks = len(walks)
    for walk in walks:
        mean_time += walk.time.hour * 60 + walk.time.minute
        # mean_minute += walk.time.minute
    mean_time = mean_time / number_walks
    mean_minute, mean_hour = math.modf(mean_time / 60)
    time = datetime.time(int(mean_hour), round(mean_minute * 60))
    habit = Habits.query.filter_by(dog=dog_uuid).first()
    if habit:
        setattr(habit, day_slot, time)
    else:
        kwargs = {'dog': dog_uuid, day_slot: time}
        habit = Habits(**kwargs)
        db.session.add(habit)

    db.session.commit()

    return Response(status=200)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
    # app.run(debug=True)
