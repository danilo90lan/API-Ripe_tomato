from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from init import db, bcrypt
from models.user import User, user_schema, users_schema
from datetime import timedelta
from flask_jwt_extended import create_access_token, get_jwt_identity

# ROUTING AREA

# we need to create the Blueprint for each decorator and then register in the main.py
auth_command = Blueprint("auth", __name__, url_prefix = "/auth")

@auth_command.route("/register", methods=["POST"])
def register_user():
    try:
        # Body of the request
        body_data = request.get_json()
        # Exctracting the password from the body of the request
        password = body_data["password"]
        # Hashing the password using bcrypt object
        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf8')
        # Create a user instance using the User model
        user = User(
            name = body_data["name"],
            email = body_data["email"],
            password = hashed_password,
            admin = body_data.get("admin")
        )
        # Add it to the session
        db.session.add(user)
        # Commit
        db.session.commit()
        # Return a message
        return jsonify(user_schema.dump(user)), 201
    except IntegrityError as e:
        return {"error": "Email already exists"}, 400


# LOGIN USER

@auth_command.route("/login", methods=["POST"])
def login_user():
    # Find the uer with that email
    body = request.get_json()

    # check if the user email is in the database
    statement = db.select(User).filter_by(email=body.get("email"))
    # execute the statement
    result = db.session.scalar(statement)

    # check if the user exists and the password matches using check_password_hash method that takes two arguments
    # (plain text password from the body request and hashed password from the database) 
    if result and bcrypt.check_password_hash(result.password, body["password"]):
        # we create an authentication token (jwt) through the module that we imported
        # the arguments are indentity=the id of the statement result converted to string and
        # the expiring session time using timedelta library. (after 1 day the login expires )
        token = create_access_token(identity=str(
            result.id), expires_delta=timedelta(days=1))

        # return the token
        # return {"token": token, "email": result.email, "admin":result.admin }
        return jsonify({"user":user_schema.dump(result), "token":token})
    # else return an error message
    else:
        return {"error":"Invalid email or password"},401
    
    
@auth_command.route("/")
def hello():
    return "Welcome to Ripe Tomatoes API"
        
# GET ALL THE USERS
@auth_command.route("/users", methods=["GET"])
def get_users():
    statement = db.select(User)
    results = db.session.scalars(statement)

    data = users_schema.dump(results)
    return jsonify(data)

def authoriseAsAdmn():
    # we receive the token and we look which user ID the token is linked to
    # get the id of the user from the jwt token using get_jwt_identity() function
    user_id = get_jwt_identity()
    #find the user in the db with the id
    statement = db.select(User).filter_by(id=user_id)
    result = db.session.scalar(statement)
    # check if the user is admin or not 
    admin = result.admin
    # return True if the admin is True of False if the admin is False
    if admin:
        return True
    else:
        return False
