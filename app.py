from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "mongodb+srv://ankitBiwas:X58NmkQssQwuymcW@cluster0.uriv4tp.mongodb.net/test"  # Change as needed

mongo = PyMongo(app)
print(mongo)
try:
    mongo.db.command("ping")
    print("MongoDB is connected")
except Exception as e:
    print("MongoDB connection failed:", e)

# Helper function to convert MongoDB document ObjectId to string for JSON responses
def jsonify_user(user):
    user["_id"] = str(user["_id"])
    return user


# User Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    role = data.get('role').lower()

    if role not in ["student", "librarian", "admin"]:
        return jsonify({"error": "Role must be either 'student' or 'librarian'"}), 400

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Check if user already exists
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 400

    # Hash password and store user
    hashed_password = generate_password_hash(password)
    user_data = {
        "name":name,
        "email": email,
        "password": hashed_password,
        "role": role,
        "bookIssued": [],
        "booksDonated": [],
        "wishlist": []
    }
    user_id = mongo.db.users.insert_one(user_data).inserted_id
    
    new_user = mongo.db.users.find_one({"_id": user_id})
    
    new_user["_id"] = str(new_user["_id"])
    return jsonify({"message": "User registered successfully", "user": new_user}), 201


# User Login Route
@app.route('/signin', methods=['POST'])
def signin():
    print("hello")
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "email": str(user['email']), "role": user["role"], "name":user["name"], "_id":str(user["_id"])}), 200


# Get User by ID
@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(jsonify_user(user))


# Update User's Wishlist, Books Issued, and Books Donated
@app.route('/user/<email>', methods=['PUT'])
def update_user(email):
    data = request.json
    update_fields = {}

    if 'wishlist' in data:
        update_fields['wishlist'] = data['wishlist']
    if 'bookIssued' in data:
        update_fields['bookIssued'] = data['bookIssued']
    if 'booksDonated' in data:
        update_fields['booksDonated'] = data['booksDonated']

    result = mongo.db.users.update_one({"email": email}, {"$set": update_fields})
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User updated successfully"}), 200


# Book CRUD Operations

# Add a Book
@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    book_data = {
        "name": data.get('name'),
        "author": data.get('author'),
        "publishedDate": data.get('publishedDate', datetime.now().strftime("%Y-%m-%d")),
    }
    book_id = mongo.db.books.insert_one(book_data).inserted_id
    return jsonify({"message": "Book added successfully", "book_id": str(book_id)}), 201


# Get All Books
@app.route('/books', methods=['GET'])
def get_books():
    books = list(mongo.db.books.find())
    for book in books:
        book["_id"] = str(book["_id"])
    return jsonify(books), 200


# Get a Book by ID
@app.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        return jsonify({"error": "Book not found"}), 404
    book["_id"] = str(book["_id"])
    return jsonify(book), 200


# Update a Book by ID
@app.route('/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.json
    update_fields = {}

    if 'name' in data:
        update_fields['name'] = data['name']
    if 'author' in data:
        update_fields['author'] = data['author']
    if 'publishedDate' in data:
        update_fields['publishedDate'] = data['publishedDate']

    result = mongo.db.books.update_one({"_id": ObjectId(book_id)}, {"$set": update_fields})
    if result.matched_count == 0:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"message": "Book updated successfully"}), 200


# Delete a Book by ID
@app.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    result = mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"message": "Book deleted successfully"}), 200


if __name__ == '__main__':
    app.run(debug=True)



