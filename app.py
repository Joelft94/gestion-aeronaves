from flask import Flask, request, jsonify, render_template, redirect, url_for
from models import db, AirplaneStatus, Aircraft, User
from datetime import datetime
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, SubmitField 
from wtforms.validators import InputRequired, Length, ValidationError
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt





app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'JACK'
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Loguear
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html', form=form)    

#Logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



#Registrarse
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('register.html', form=form)


class RegisterForm(FlaskForm):
    username = StringField('username',validators=[InputRequired(), Length(min=4, max=15)], render_kw={"placeholder": "Username"})
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')
    
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        
        if existing_user_username:
            raise ValidationError('El usuario ya existe por favor elija otro nombre de usuario')
        
        
    
    

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError('Ese usuario ya existe, por favor elija.')
        

class LoginForm(FlaskForm):
    username = StringField('username',validators=[InputRequired(), Length(min=4, max=15)], render_kw={"placeholder": "Username"})
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')
    




# Index
@app.route('/')
@login_required
def index():
    aircrafts = Aircraft.query.all()
    return render_template('index.html', aircrafts=aircrafts, selected_aircraft_id=None)


# Ver Aeronaves
@app.route('/aircraft/<int:aircraft_id>', methods=['GET'])
@login_required
def view_aircraft(aircraft_id):
    aircraft = Aircraft.query.get_or_404(aircraft_id)
    statuses = AirplaneStatus.query.filter_by(aircraft_id=aircraft_id).all()
    return render_template('view_aircraft.html', aircraft=aircraft, statuses=statuses)


# Agregar informacion de vuelo
@app.route('/aircraft/<int:aircraft_id>/add_flight', methods=['POST'])
@login_required
def add_flight(aircraft_id):
    try:
        data = request.form
        
        #Para debug vemos el contenido de data        
        # print("Raw form data:", data)
        
        
        # Convertir horas a formato datetime.time para almacenar en la base de datos ya que no acepta el formato HH:MM
        departure_hour = datetime.strptime(data['departure_hour'], '%H:%M').time()
        arrival_hour = datetime.strptime(data['arrival_hour'], '%H:%M').time()

        #Para debug vemos el contenido de departure_hour y arrival_hour
        print("Converted departure_hour:", departure_hour)
        print("Converted arrival_hour:", arrival_hour)

        new_airplane_status = AirplaneStatus(
            pilot=data['pilot'],
            copilot=data['copilot'],
            departure_hour=departure_hour,
            arrival_hour=arrival_hour,
            total_flown_hours=float(data['total_flown_hours']),
            departure_place=data['departure_place'],
            flight_type=data['flight_type'],
            observation=data['observation'],
            aircraft_id=aircraft_id
        )
        db.session.add(new_airplane_status)
        db.session.commit()
        return redirect(url_for('view_aircraft', aircraft_id=aircraft_id))
    except Exception as e:
        db.session.rollback()
        # Retornar mensaje de error en formato JSON si es que falla
        return jsonify({'error': str(e)}), 500

@app.route('/consulta', methods=['GET'])
@login_required
def consult_airplane_status():
    statuses = AirplaneStatus.query.all()
    return render_template('consult.html', statuses=statuses)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_airplane_status(id):
    status = AirplaneStatus.query.get(id)
    if request.method == 'POST':
        try:
            # Update de los campos de status con los datos del formulario provistos por el usuario al editar
            status.pilot = request.form['pilot']
            status.copilot = request.form['copilot']
            

                
            # Determinar el formato del tiempo de acuerdo a si el usuario ingreso HH:MM o HH:MM:SS
            time_str_departure = request.form['departure_hour']
            time_str_arrival = request.form['arrival_hour']
            
            
            # Compara si viene un ":" seguido del MM para saber si viene HH:MM:SS o HH:MM
            time_format = '%H:%M:%S' if time_str_departure.count(':') == 2 else '%H:%M'
            
            
            
            
            #Aca transformamos el string HH:MM a datetime.time como en el caso de add_flight
            status.departure_hour = datetime.strptime(time_str_departure, time_format).time()
            status.arrival_hour = datetime.strptime(time_str_arrival, time_format).time()
            
            status.total_flown_hours = float(request.form['total_flown_hours'])
            status.departure_place = request.form['departure_place']
            status.flight_type = request.form['flight_type']
            status.observation = request.form['observation']

            db.session.commit()
            return redirect(url_for('view_aircraft', aircraft_id=status.aircraft_id))
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    return render_template('edit.html', status=status)

# Borrar vuelo de aeronave
@app.route('/borrar/<int:id>', methods=['POST'])
@login_required
def delete_airplane_status(id):
    status = AirplaneStatus.query.get(id)
    db.session.delete(status)
    db.session.commit()
    return jsonify({'message': 'Vuelo eliminado exitosamente!'})

# Agregar aeronave
@app.route('/add_aircraft', methods=['GET', 'POST'])
@login_required
def add_aircraft():
    if request.method == 'POST':
        data = request.form
        new_aircraft = Aircraft(name=data['name'])
        db.session.add(new_aircraft)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_aircraft.html')

# Borrar aeronave
@app.route('/aircraft/<int:aircraft_id>/delete', methods=['POST'])
@login_required
def delete_aircraft(aircraft_id):
    try:
        aircraft = Aircraft.query.get(aircraft_id)
        db.session.delete(aircraft)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=9000, debug=True)
