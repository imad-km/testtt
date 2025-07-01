from os import access
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT, HTTP_404_NOT_FOUND
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from flasgger import swag_from
from src.database import User, db, Doctor, Ticket, TicketLog, Admin, Feedback
from datetime import datetime, timedelta
import random
import string
from flask_cors import CORS, cross_origin  # Add this import
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

cred = credentials.Certificate("zitado.json")
firebase_admin.initialize_app(cred)

def sendkm(device_token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=device_token,
        data=data or {}  # Convert None to empty dict
    )
    
    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return response
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.get('/feedback/<int:doctor_id>')
@jwt_required()
def get_feedback(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    feedbacks = Feedback.query.filter_by(doctor_id=doctor_id).all()
    result = {}
    for fb in feedbacks:
        fullname = fb.firstname + " " + fb.lastname
        result[fullname] = {"rate": fb.rating, "comment": fb.comment, "create_at": fb.created_at}
    return jsonify(result), HTTP_200_OK

@auth.post('/feedback/sub')
@jwt_required()
def submit_feedback():
    user_id = get_jwt_identity()
    user = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND

    doctor_id = request.json.get('doctor_id')
    comment = request.json.get('comment', '').strip()
    try:
        rating = int(request.json.get('rating'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Rating must be an integer'}), HTTP_400_BAD_REQUEST

    if not doctor_id or not comment or rating not in [1, 2, 3, 4, 5]:
        return jsonify({'error': 'Missing or invalid fields'}), HTTP_400_BAD_REQUEST

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    existing_feedback = Feedback.query.filter_by(doctor_id=doctor_id, identify=user_id).first()
    if existing_feedback:
        return jsonify({'error': 'You already submitted feedback for this doctor'}), HTTP_409_CONFLICT

    feedback = Feedback(
        doctor_id=doctor_id,
        firstname=user.firstnameen,
        lastname=user.lastnameen,
        rating=rating,
        comment=comment,
        identify=user_id
    )
    db.session.add(feedback)
    db.session.commit()

    all_feedbacks = Feedback.query.filter_by(doctor_id=doctor_id).all()
    total_rating = sum(fb.rating for fb in all_feedbacks)
    average_rating = round(total_rating / len(all_feedbacks))

    doctor.rate = str(average_rating)
    db.session.commit()

    return jsonify({'message': 'Feedback submitted', 'new_rating': average_rating}), HTTP_201_CREATED


@auth.post('/register')
def register():
    firstnameen = request.json['firstnameen']
    lastnameen = request.json['lastnameen']
    email = request.json['email']
    city = request.json['city']
    password = request.json['password']
    identify = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

    role = "client"
    if len(password) < 6:
        return jsonify({'error': "Password is too short"}), HTTP_400_BAD_REQUEST
    

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': "phone number is taken"}), HTTP_409_CONFLICT
    
    pwd_hash = generate_password_hash(password)

    user = User(firstnameen=firstnameen, lastnameen=lastnameen, password=pwd_hash, email=email, identify=identify, role=role, city=city)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': "User created",
        'user': {
            'firstname': firstnameen, "lastname": lastnameen
        }
    }), HTTP_201_CREATED

@auth.post('/doctor/register')
@cross_origin()
def register_doctor():
    firstname = request.json.get('firstname', '').strip()
    lastname = request.json.get('lastname', '').strip()
    date_birthday = request.json.get('date_birthday', '').strip()
    specialty = request.json.get('specialty', '').strip()
    email = request.json.get('email', '').strip()
    city = request.json.get('city', '').strip()
    adress = request.json.get('adress', '').strip()
    localisation = request.json.get('localisation', '').strip()
    image_clinik = request.json.get('image_clinik', '').strip()
    password = request.json.get('password', '').strip()
    
    # New fields
    image = request.json.get('image', '').strip()
    price = request.json.get('price', '').strip()
    description = request.json.get('description', '').strip()
    time_start = request.json.get('time_start', '').strip()
    time_end = request.json.get('time_end', '').strip()
    
    identify = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    role = "doctor"

    if len(password) < 6:
        return jsonify({'error': "Password is too short"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() or Doctor.query.filter_by(email=email).first():
        return jsonify({'error': "Phone or email already exist"}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    doctor = Doctor(
        firstname=firstname,
        lastname=lastname,
        date_birthday=date_birthday,
        specialty=specialty,
        email=email,
        password=pwd_hash,
        role=role,
        city=city,
        adress=adress,
        image_clinik=image_clinik,
        localisation=localisation,
        identify=identify,
        status="waiting",
        # New fields
        image=image,
        price=price,
        description=description,
        time_start=time_start,
        time_end=time_end
    )
    db.session.add(doctor)
    db.session.commit()

    return jsonify({
        'message': "Doctor registration request sent",
        'doctor': {
            'firstname': firstname,
            'lastname': lastname,
            'specialty': specialty,
            'image': image,
            'price': price,
            'description': description,
            'working_hours': f"{time_start} to {time_end}"
        }
    }), HTTP_201_CREATED

@auth.post('/login')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    n_token = request.json.get('token', '')
    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            user.n_token = n_token
            db.session.commit()

            refresh = create_refresh_token(identity=user.identify)
            access_expiry = timedelta(days=30)

            access = create_access_token(identity=user.identify, expires_delta=access_expiry)
            access_expiry_seconds = access_expiry.total_seconds()
            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'access_expiry': access_expiry_seconds,
                }
            }), HTTP_200_OK

    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED

@auth.post('/doctor/login')
@cross_origin()
def login_doctor():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    doctor = Doctor.query.filter_by(email=email).first()

    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    if doctor.status != 'accept':
        return jsonify({'error': 'Account not approved yet'}), HTTP_401_UNAUTHORIZED

    is_pass_correct = check_password_hash(doctor.password, password)

    if is_pass_correct:
        access_expiry = timedelta(days=30)
        access_token = create_access_token(identity=doctor.identify, expires_delta=access_expiry)
        refresh_token = create_refresh_token(identity=doctor.identify)
        access_expiry_seconds = access_expiry.total_seconds()

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_expiry': access_expiry_seconds,
            'id': doctor.id,
            'firstname': doctor.firstname,
            'lastname': doctor.lastname,
            'email': doctor.email,
            'specialty': doctor.specialty,
        }), HTTP_200_OK

    return jsonify({'error': 'Invalid credentials'}), HTTP_401_UNAUTHORIZED

@auth.post('/admin/login')
@cross_origin()
def login_admin():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    admin = Admin.query.filter_by(email=email).first()

    if not admin:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    is_pass_correct = check_password_hash(admin.password, password)

    if is_pass_correct:
        access_expiry = timedelta(days=30)
        access_token = create_access_token(identity=admin.identify, expires_delta=access_expiry)
        refresh_token = create_refresh_token(identity=admin.identify)
        access_expiry_seconds = access_expiry.total_seconds()

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_expiry': access_expiry_seconds,
            'firstname': admin.firstnameen,
            'lastname': admin.lastnameen,
            'email': admin.email,
        }), HTTP_200_OK

    return jsonify({'error': 'Invalid credentials'}), HTTP_401_UNAUTHORIZED

@auth.get("/me")
@jwt_required()
@cross_origin()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(identify=user_id).first()
    if user:
        return jsonify({
            'perm': user.role,
            'id': user.id,
            'firstname': user.firstnameen,
            'lastname': user.lastnameen,
            'email': user.email,
            'city': user.city,
            'create_at': user.created_at,
        }), HTTP_200_OK
    doctor = Doctor.query.filter_by(identify=user_id).first()
    if doctor:
        return jsonify({
            'perm': doctor.role,
            'id': doctor.id,
            'firstname': doctor.firstname,
            'lastname': doctor.lastname,
            'email': doctor.email,
            'specialty': doctor.specialty,
            'status': doctor.status,
            'description': doctor.description,
            'timeStart': doctor.time_start,
            'timeEnd': doctor.time_end,
            'consultationPrice': doctor.price,
            'selectedDays': doctor.weak,
            'imageFile': doctor.image
        }), HTTP_200_OK
    admin = Admin.query.filter_by(identify=user_id).first()
    if admin:
        return jsonify({
            'perm': 'admin',
            'firstname': admin.firstnameen,
            'lastname': admin.lastnameen,
            'email': admin.email,
            'created_at': admin.created_at,
        }), HTTP_200_OK

    return jsonify({'error': 'Invalid token '}), HTTP_404_NOT_FOUND



@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'access': access
    }), HTTP_200_OK



@auth.get('/admin/doctor_requests')
@jwt_required()
@cross_origin()
def get_doctor_requests():
    admin_id = get_jwt_identity()
    admin = Admin.query.filter_by(id=admin_id).first()

    if not admin or admin.role != "admin":
        return jsonify({'error': "Access forbidden"}), HTTP_401_UNAUTHORIZED

    doctor_requests = Doctor.query.filter_by(status="waiting").all()

    return jsonify({
        'doctor_requests': [
            {
                'id': doctor.id,
                'firstname': doctor.firstname,
                'lastname': doctor.lastname,
                'email': doctor.email,
                'specialty': doctor.specialty,
                'date_birthday': doctor.date_birthday,
                'status': doctor.status
            } for doctor in doctor_requests
        ]
    }), HTTP_200_OK


@auth.post('/admin/approve_doctor')
@jwt_required()
def approve_doctor():
    admin_id = get_jwt_identity()
    admin = Admin.query.filter_by(identify=admin_id).first()

    if not admin or admin.role != "admin":
        return jsonify({'error': "Access forbidden"}), HTTP_401_UNAUTHORIZED

    doctor_id = request.json.get('doctor_id')
    action = request.json.get('action', '').strip().lower()  # 'accept' or 'decline'

    doctor = Doctor.query.filter_by(identify=doctor_id).first()

    if not doctor:
        return jsonify({'error': "Doctor not found"}), HTTP_404_NOT_FOUND

    if action == "accept":
        doctor.status = "accepted"
    elif action == "decline":
        doctor.status = "declined"
    else:
        return jsonify({'error': "Invalid action"}), HTTP_400_BAD_REQUEST

    db.session.commit()

    return jsonify({
        'message': f"Doctor registration {action}ed successfully",
        'doctor': {
            'id': doctor.id,
            'firstname': doctor.firstname,
            'lastname': doctor.lastname,
            'status': doctor.status
        }
    }), HTTP_200_OK
@auth.get('/doctor/<int:doctor_id>')
@jwt_required()
def get_doctor_info(doctor_id):
    # Get the current user's identity
    user_id = get_jwt_identity()
    
    # Get the doctor by the given doctor_id
    doctor = Doctor.query.get(doctor_id)
    
    if not doctor or doctor.status == 'waiting':
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    # Check if user has any ticket logs with this doctor
    is_exist = "0"
    if user_id:
        existing_log = TicketLog.query.filter_by(
            doctor_id=doctor_id,
            identify=user_id
        ).first()
        if existing_log:
            is_exist = "1"
    return jsonify({
        'doctor': {
            'id': doctor.id,
            'firstname': doctor.firstname,
            'lastname': doctor.lastname,
            'email': doctor.email,
            'specialty': doctor.specialty,
            'price': doctor.price if hasattr(doctor, 'price') else None,
            'time_start': doctor.time_start,
            'time_end': doctor.time_end,
            'image': doctor.image if hasattr(doctor, 'image') else None,
            'date_birthday': doctor.date_birthday,
            'status': doctor.status,
            'weak': doctor.weak,
            'city': doctor.city,
            'localisation': doctor.localisation,
            'description': doctor.description,
            'rate': doctor.rate,
            'isexist': is_exist  # Add this field
        }
    }), HTTP_200_OK

@auth.get('/doctors')
@jwt_required()
def get_doctors():
    # Filter out doctors with status == 'waiting'
    doctors = Doctor.query.filter(Doctor.status != 'waiting').all()
    # Get the current user's identity
    user_id = get_jwt_identity()

    doctor_list = []
    for doctor in doctors:
        # Check if user has any ticket logs with this doctor
        is_exist = "0"
        if user_id:
            existing_log = TicketLog.query.filter_by(
                doctor_id=doctor.id,
                identify=user_id
            ).first()
            if existing_log:
                is_exist = "1"
        
        doctor_list.append({
            'id': doctor.id,
            'firstname': doctor.firstname,
            'lastname': doctor.lastname,
            'email': doctor.email,
            'specialty': doctor.specialty,
            'price': doctor.price if hasattr(doctor, 'price') else None,
            'time_start': doctor.time_start,
            'time_end': doctor.time_end,
            'image': doctor.image if hasattr(doctor, 'image') else None,
            'date_birthday': doctor.date_birthday,
            'status': doctor.status,
            'weak': doctor.weak,
            'city': doctor.city,
            'localisation': doctor.localisation,
            'description': doctor.description,
            'isexist': is_exist,
            'rate': doctor.rate,
        })

    return jsonify({
        'doctors': doctor_list
    }), HTTP_200_OK


@auth.get('/doctor/myticket')
@jwt_required()
@cross_origin()
def get_my_tickets():
    identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=identity).first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND
    dfullname = doctor.firstname + " " + doctor.lastname
    tickets = Ticket.query.filter_by(doctor_id=doctor.id).all()
    if not tickets:
        return jsonify({'message': 'No tickets found for this doctor'}), HTTP_200_OK
    return jsonify({
        'doctor_id': doctor.id,
        'doctor_name': dfullname,
        'tickets': [
            {
                'ticket_number': ticket.ticket_number,
                'ticket_code': ticket.ticket_code,
                'ticket_phone': ticket.number,
                'created_at': ticket.created_at,
                'fullname': ticket.fullname,
                'status': ticket.status
            } for ticket in tickets
        ]
    }), HTTP_200_OK


@auth.post('/doctor/check')
@jwt_required()
@cross_origin()
def check_ticket_status():
    doctor_identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=doctor_identity).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    ticket_code = request.json.get('ticket_code')
    new_status = request.json.get('new_status')  # Expected to be '0', '1', or '2'

    if new_status not in ['0', '1', '2']:
        return jsonify({'error': 'Invalid status'}), HTTP_400_BAD_REQUEST

    # Find ticket by ticket_code and check if it belongs to this doctor
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket or ticket.doctor_id != doctor.id:
        return jsonify({'error': 'Ticket not found or not assigned to this doctor'}), HTTP_404_NOT_FOUND

    # Update corresponding ticket log status first
    ticket_log = TicketLog.query.filter_by(
        doctor_id=doctor.id,
        ticket_number=ticket.ticket_number
    ).first()
    
    if ticket_log:
        ticket_log.status = new_status
        db.session.commit()

    # Delete the ticket from Ticket table (but it remains in TicketLog)
    db.session.delete(ticket)
    db.session.commit()

    return jsonify({
        'message': 'ok',
        'ticket_code': ticket_code,
        'status': new_status
    }), HTTP_200_OK

@auth.post('/ticket/del')
@jwt_required()
def delete_ticket():
    user_id = get_jwt_identity()
    ticket_code = request.json.get('ticket_code')

    if not ticket_code:
        return jsonify({'error': 'Ticket code is required'}), HTTP_400_BAD_REQUEST

    # Find the ticket by ticket_code
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), HTTP_404_NOT_FOUND

    # Check if the requesting user is the doctor who owns this ticket
    doctor = Doctor.query.filter_by(identify=user_id).first()
    if not doctor or doctor.id != ticket.doctor_id:
        return jsonify({'error': 'Unauthorized to delete this ticket'}), HTTP_401_UNAUTHORIZED

    # Delete the ticket and corresponding log
    TicketLog.query.filter_by(
        doctor_id=ticket.doctor_id,
        ticket_number=ticket.ticket_number
    ).delete()
    
    db.session.delete(ticket)
    db.session.commit()

    return jsonify({
        'message': 'Ticket deleted successfully',
        'ticket_code': ticket_code
    }), HTTP_200_OK
@auth.post('/ticket')
@jwt_required()
def create_ticket():
    user_id = get_jwt_identity()
    user = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND

    doctor_id = request.json['doctor_id']
    n_token = request.json.get('token', '')
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    # Check if user already has an active ticket with this doctor
    existing_ticket = Ticket.query.filter_by(
        identify=user_id,
        doctor_id=doctor_id,
        status='0'  # Only check for active tickets (status '0')
    ).first()

    if existing_ticket:
        return jsonify({
            'error': 'You already have an active ticket with this doctor',
            'existing_ticket': {
                'ticket_number': existing_ticket.ticket_number,
                'ticket_code': existing_ticket.ticket_code,
                'created_at': existing_ticket.created_at
            }
        }), HTTP_409_CONFLICT

    dfullname = doctor.firstname + " " + doctor.lastname
    last_ticket = Ticket.query.filter_by(doctor_id=doctor_id).order_by(Ticket.ticket_number.desc()).first()
    ticket_number = 1 if not last_ticket else last_ticket.ticket_number + 1

    ticket_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    fullname = user.firstnameen + " " + user.lastnameen
    status = "0"

    now = datetime.now()
    expiry_date = now.replace(hour=23, minute=59, second=59, microsecond=0)

    ticket = Ticket(
        doctor_id=doctor_id, 
        number=user.email,
        ticket_number=ticket_number, 
        ticket_code=ticket_code, 
        fullname=fullname, 
        status=status,
        expiry_date=expiry_date,
        n_token=n_token,
        identify=user.identify
    )
    db.session.add(ticket)
    db.session.commit()

    ticket_log = TicketLog(
        doctor_id=doctor.id,
        number=user.email,
        ticket_number=ticket.ticket_number,
        ticket_code=ticket.ticket_code,
        fullname=ticket.fullname,
        status=ticket.status,
        created_at=ticket.created_at,
        expiry_date=ticket.expiry_date,
        identify=user.identify
    )
    db.session.add(ticket_log)
    db.session.commit()

    return jsonify({
        'doctor_id': doctor.id,
        'ticket': ticket.ticket_number,
        'ticket_code': ticket.ticket_code,
        'doctor_name': dfullname,
        'fullname': ticket.fullname,
        'status': status,
        'created_at': ticket.created_at,
        'expiry_date': ticket.expiry_date
    }), HTTP_201_CREATED


@auth.post('/myticket/del')
@jwt_required()
def delete_my_ticket():
    user_id = get_jwt_identity()
    ticket_code = request.json.get('ticket_code')

    if not ticket_code:
        return jsonify({'error': 'Ticket code is required'}), HTTP_400_BAD_REQUEST

    # Find the ticket by ticket_code and user identity
    ticket = Ticket.query.filter_by(ticket_code=ticket_code, identify=user_id).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), HTTP_404_NOT_FOUND

    doctor_id = ticket.doctor_id
    ticket_number = ticket.ticket_number

    # Delete the ticket
    db.session.delete(ticket)

    db.session.commit()

    return jsonify({
        'message': 'Your ticket was successfully deleted',
        'ticket_code': ticket_code
    }), HTTP_200_OK

@auth.get('/myticket')
@jwt_required()
def get_user_tickets():
    user_id = get_jwt_identity()
    tickets = Ticket.query.filter_by(identify=user_id).all()

    result = []
    for ticket in tickets:
        doctor = Doctor.query.get(ticket.doctor_id)
        dfullname = doctor.firstname + " " + doctor.lastname
        result.append({
            'doctor_id': doctor.id,
            'ticket': ticket.ticket_number,
            'ticket_code': ticket.ticket_code,
            'doctor_name': dfullname,
            'fullname': ticket.fullname,
            'status': ticket.status,
            'created_at': ticket.created_at,
            'expiry_date': ticket.expiry_date
        })

    return jsonify(result), HTTP_200_OK
@auth.post('/doctor/come')
@jwt_required()
@cross_origin()
def notify_user():
    doctor_identity = get_jwt_identity()
    
    doctor = Doctor.query.filter_by(identify=doctor_identity).first()
    if not doctor:
        return jsonify({'error': 'Only doctors can access this endpoint'}), HTTP_401_UNAUTHORIZED
    
    ticket_code = request.json.get('ticket_code')
    if not ticket_code:
        return jsonify({'error': 'Ticket code is required'}), HTTP_400_BAD_REQUEST

    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), HTTP_404_NOT_FOUND

    user = User.query.filter_by(identify=ticket.identify).first()
    if not user or not user.n_token:
        return jsonify({'error': 'User notification token not found'}), HTTP_404_NOT_FOUND
    
    n_token = ticket.n_token
    doctorrr = doctor.firstname + " " + doctor.lastname
    fullnameaa = user.firstnameen + " " + user.lastnameen
    desc = f"مرحبًا {fullnameaa}، لقد حان موعدك الآن مع الطبيب {doctorrr}. نرجو التوجه إلى العيادة في أقرب وقت."
    sendkm(
        device_token=n_token,
        title="تذكير بالموعد الطبي",
        body=desc,
        data={"click_action": "OPEN_CHAT", "user_id": "123"}
    )
    return jsonify({
        'status': 'ok',
    }), HTTP_200_OK

@auth.post('/live')
@jwt_required()
def get_live_status():
    doctor_id = request.json.get('doctor_id')
    ticket_code = request.json.get('ticket_code')

    if not doctor_id or not ticket_code:
        return jsonify({'error': 'doctor_id and ticket_code are required'}), HTTP_400_BAD_REQUEST

    # Find the doctor
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    # Find the ticket
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), HTTP_404_NOT_FOUND

    return jsonify({
        'doctor_name': f"{doctor.firstname} {doctor.lastname}",
        'doctor_image': doctor.image,
        'doctor_speciality': doctor.specialty,
        'live': doctor.ticket,
        'mynumber': ticket.ticket_number
    }), HTTP_200_OK

@auth.post('/doctor/setting')
@jwt_required()
def update_doctor_settings():
    doctor_identity = get_jwt_identity()
    
    doctor = Doctor.query.filter_by(identify=doctor_identity).first()
    if not doctor:
        return jsonify({'error': 'Only doctors can access this endpoint'}), HTTP_401_UNAUTHORIZED

    # Get data from request
    data = request.json
    
    # Update fields if they exist in the request
    if 'description' in data:
        doctor.description = data['description']
    if 'timeStart' in data:
        doctor.time_start = f"{data['timeStart']} AM"
    if 'timeEnd' in data:
        doctor.time_end = f"{data['timeEnd']} PM"
    if 'consultationPrice' in data:
        doctor.price = f"{data['consultationPrice']}DA"
    if 'selectedDays' in data:
        doctor.weak = data['selectedDays']
    
    # Handle image file (assuming it's passed as a base64 string or URL)
    if 'image' in data and data['image'] is not None:
        doctor.image = data['image']
    
    # Commit changes to database
    db.session.commit()
    
    return jsonify({
        'status': 'ok',
        'message': 'Doctor settings updated successfully',
        'doctor': {
            'description': doctor.description,
            'timeStart': doctor.time_start,
            'timeEnd': doctor.time_end,
            'consultationPrice': doctor.price,
            'selectedDays': doctor.weak,
            'imageFile': doctor.image
        }
    }), HTTP_200_OK

@auth.get('/doctor/logticket')
@jwt_required()
@cross_origin()
def get_doctor_ticket_logs():
    identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=identity).first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    dfullname = doctor.firstname + " " + doctor.lastname

    ticket_logs = db.session.query(TicketLog).filter(
        TicketLog.doctor_id == doctor.id,
        TicketLog.status != '0'
    ).all()

    if not ticket_logs:
        return jsonify({'message': 'No ticket logs found for this doctor'}), HTTP_200_OK

    return jsonify({
        'doctor_id': doctor.id,
        'doctor_name': dfullname,
        'tickets': [
            {
                'ticket_number': log.ticket_number,
                'ticket_code': log.ticket_code,
                'created_at': log.created_at,
                'fullname': log.fullname,
                'status': log.status,
                'expiry_date': log.expiry_date
            } for log in ticket_logs
        ]
    }), HTTP_200_OK

@auth.post('/doctor/newticket')
@jwt_required()
@cross_origin()
def create_manual_ticket():
    doctor_identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=doctor_identity).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND

    # Get patient details from request
    firstname = request.json.get('firstname', '').strip()
    lastname = request.json.get('lastname', '').strip()
    phone = request.json.get('Phone', '')  # Optional field

    if not firstname or not lastname:
        return jsonify({'error': 'Firstname and lastname are required'}), HTTP_400_BAD_REQUEST

    # Generate ticket details
    last_ticket = Ticket.query.filter_by(doctor_id=doctor.id).order_by(Ticket.ticket_number.desc()).first()
    ticket_number = 1 if not last_ticket else last_ticket.ticket_number + 1
    ticket_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    fullname = f"{firstname} {lastname}"
    status = "0"

    now = datetime.now()
    expiry_date = now.replace(hour=23, minute=59, second=59, microsecond=0)

    # Create the ticket
    ticket = Ticket(
        doctor_id=doctor.id,
        number=phone,
        ticket_number=ticket_number,
        ticket_code=ticket_code,
        fullname=fullname,
        status=status,
        expiry_date=expiry_date,
        identify=None  # No user identity since this is a manual ticket
    )
    db.session.add(ticket)

    # Also create a ticket log
    ticket_log = TicketLog(
        doctor_id=doctor.id,
        ticket_number=ticket.ticket_number,
        ticket_code=ticket.ticket_code,
        fullname=ticket.fullname,
        status=ticket.status,
        created_at=ticket.created_at,
        expiry_date=ticket.expiry_date,
        identify=None
    )
    db.session.add(ticket_log)
    db.session.commit()

    return jsonify({
        'doctor_id': doctor.id,
        'ticket_number': ticket.ticket_number,
        'ticket_code': ticket.ticket_code,
        'patient_name': fullname,
        'phone': phone,
        'status': status,
        'created_at': ticket.created_at,
        'expiry_date': ticket.expiry_date
    }), HTTP_201_CREATED
@auth.get('/doctor/nowticket')
@jwt_required()
@cross_origin()
def get_current_ticket():
    identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=identity).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND
    
    # Find the first non-skipped ticket (skip is not "1")
    current_ticket = Ticket.query.filter(
        Ticket.doctor_id == doctor.id,
        db.or_(Ticket.skip != "1", Ticket.skip == None)
    ).order_by(Ticket.ticket_number.asc()).first()

    if not current_ticket:
        return jsonify({'message': 'No active tickets in queue'}), HTTP_200_OK

    return jsonify({
        'doctor_id': doctor.id,
        'ticket_number': current_ticket.ticket_number,
        'ticket_code': current_ticket.ticket_code,
        'fullname': current_ticket.fullname,
        'status': current_ticket.status,
        'created_at': current_ticket.created_at,
        'expiry_date': current_ticket.expiry_date,
        'skip': current_ticket.skip if current_ticket.skip else "0"
    }), HTTP_200_OK
@auth.post('/doctor/skip')
@jwt_required()
@cross_origin()
def skip_ticket():
    identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=identity).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND
    
    ticket_code = request.json.get('ticket_code')
    if not ticket_code:
        return jsonify({'error': 'Ticket code is required'}), HTTP_400_BAD_REQUEST

    ticket = Ticket.query.filter_by(
        doctor_id=doctor.id,
        ticket_code=ticket_code
    ).first()

    if not ticket:
        return jsonify({'error': 'Ticket not found'}), HTTP_404_NOT_FOUND

    ticket.skip = "1"  # Mark as skipped
    db.session.commit()

    return jsonify({
        'message': 'Ticket marked as skipped',
        'ticket_code': ticket_code,
        'ticket_number': ticket.ticket_number
    }), HTTP_200_OK

@auth.get('/doctor/homeinfo')
@jwt_required()
@cross_origin()
def get_doctor_home_info():
    identity = get_jwt_identity()
    doctor = Doctor.query.filter_by(identify=identity).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), HTTP_404_NOT_FOUND
    
    # Count confirmed tickets (status = '1')
    total_confirmed = TicketLog.query.filter_by(
        doctor_id=doctor.id,
        status='1'
    ).count()
    
    # Count canceled tickets (status = '2')
    total_canceled = TicketLog.query.filter_by(
        doctor_id=doctor.id,
        status='2'
    ).count()
    
    # Count feedbacks
    total_feedbacks = Feedback.query.filter_by(
        doctor_id=doctor.id
    ).count()
    
    return jsonify({
        'total_confirmed': total_confirmed,
        'total_canceled': total_canceled,
        'total_feedbacks': total_feedbacks
    }), HTTP_200_OK