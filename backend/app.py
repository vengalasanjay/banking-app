import os
import random
import string
from datetime import timedelta

import bcrypt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy

db  = SQLAlchemy()
jwt = JWTManager()


# ── Models ──────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    email         = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(100), nullable=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())
    accounts      = db.relationship("Account", back_populates="user", lazy=True)


class Account(db.Model):
    __tablename__ = "accounts"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    account_type   = db.Column(db.String(10), default="savings")
    balance        = db.Column(db.Numeric(15, 2), default=0.00)
    created_at     = db.Column(db.DateTime, server_default=db.func.now())
    user           = db.relationship("User", back_populates="accounts")
    transactions   = db.relationship("Transaction", back_populates="account", lazy=True)


class Transaction(db.Model):
    __tablename__ = "transactions"
    id                = db.Column(db.Integer, primary_key=True)
    account_id        = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    type              = db.Column(db.String(12), nullable=False)
    amount            = db.Column(db.Numeric(15, 2), nullable=False)
    description       = db.Column(db.String(255))
    reference_account = db.Column(db.String(20))
    created_at        = db.Column(db.DateTime, server_default=db.func.now())
    account           = db.relationship("Account", back_populates="transactions")


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _gen_account_number():
    return "ACC" + "".join(random.choices(string.digits, k=10))

def _hash_password(plain):
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def _account_dict(acc):
    return {
        "id": acc.id,
        "account_number": acc.account_number,
        "account_type": acc.account_type,
        "balance": float(acc.balance),
        "created_at": acc.created_at.isoformat() if acc.created_at else None,
    }

def _tx_dict(tx):
    return {
        "id": tx.id,
        "type": tx.type,
        "amount": float(tx.amount),
        "description": tx.description or "",
        "reference_account": tx.reference_account or "",
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }


# ── Application factory ─────────────────────────────────────────────────────────
def create_app(config=None):
    app = Flask(__name__)

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "bankingdb")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "rootpassword")

    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET", "change-me"))
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=8))

    if config:
        app.config.update(config)

    CORS(app, origins="*")
    db.init_app(app)
    jwt.init_app(app)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "banking-backend", "version": "1.0.0"})

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json(silent=True) or {}
        for field in ("username", "email", "password", "full_name"):
            if not data.get(field):
                return jsonify({"error": f"Field '{field}' is required"}), 400
        if User.query.filter_by(username=data["username"]).first():
            return jsonify({"error": "Username already taken"}), 409
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already registered"}), 409
        user = User(
            username=data["username"], email=data["email"],
            password_hash=_hash_password(data["password"]), full_name=data["full_name"],
        )
        db.session.add(user)
        db.session.flush()
        account = Account(user_id=user.id, account_number=_gen_account_number(),
                          account_type="savings", balance=0.00)
        db.session.add(account)
        db.session.commit()
        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token,
                        "user": {"id": user.id, "username": user.username,
                                 "full_name": user.full_name}}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        user = User.query.filter_by(username=username).first()
        if not user or not _verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid username or password"}), 401
        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token,
                        "user": {"id": user.id, "username": user.username,
                                 "full_name": user.full_name}})

    @app.route("/api/accounts", methods=["GET"])
    @jwt_required()
    def list_accounts():
        uid = int(get_jwt_identity())
        return jsonify([_account_dict(a) for a in Account.query.filter_by(user_id=uid).all()])

    @app.route("/api/accounts", methods=["POST"])
    @jwt_required()
    def create_account():
        uid = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}
        acc_type = data.get("account_type", "savings")
        if acc_type not in ("savings", "checking"):
            return jsonify({"error": "account_type must be 'savings' or 'checking'"}), 400
        account = Account(user_id=uid, account_number=_gen_account_number(),
                          account_type=acc_type, balance=0.00)
        db.session.add(account)
        db.session.commit()
        return jsonify(_account_dict(account)), 201

    @app.route("/api/accounts/<int:account_id>/transactions", methods=["GET"])
    @jwt_required()
    def get_transactions(account_id):
        uid = int(get_jwt_identity())
        acc = Account.query.filter_by(id=account_id, user_id=uid).first()
        if not acc:
            return jsonify({"error": "Account not found"}), 404
        txs = (Transaction.query.filter_by(account_id=account_id)
               .order_by(Transaction.created_at.desc()).limit(50).all())
        return jsonify([_tx_dict(t) for t in txs])

    @app.route("/api/accounts/<int:account_id>/deposit", methods=["POST"])
    @jwt_required()
    def deposit(account_id):
        uid = int(get_jwt_identity())
        acc = Account.query.filter_by(id=account_id, user_id=uid).first()
        if not acc:
            return jsonify({"error": "Account not found"}), 404
        data   = request.get_json(silent=True) or {}
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
        acc.balance = float(acc.balance) + amount
        tx = Transaction(account_id=account_id, type="deposit", amount=amount,
                         description=data.get("description", "Deposit"))
        db.session.add(tx)
        db.session.commit()
        return jsonify({"balance": float(acc.balance), "transaction": _tx_dict(tx)})

    @app.route("/api/accounts/<int:account_id>/withdraw", methods=["POST"])
    @jwt_required()
    def withdraw(account_id):
        uid = int(get_jwt_identity())
        acc = Account.query.filter_by(id=account_id, user_id=uid).first()
        if not acc:
            return jsonify({"error": "Account not found"}), 404
        data   = request.get_json(silent=True) or {}
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
        if float(acc.balance) < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        acc.balance = float(acc.balance) - amount
        tx = Transaction(account_id=account_id, type="withdrawal", amount=amount,
                         description=data.get("description", "Withdrawal"))
        db.session.add(tx)
        db.session.commit()
        return jsonify({"balance": float(acc.balance), "transaction": _tx_dict(tx)})

    @app.route("/api/transfer", methods=["POST"])
    @jwt_required()
    def transfer():
        uid  = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}
        from_id = data.get("from_account_id")
        to_num  = data.get("to_account_number", "").strip()
        amount  = float(data.get("amount", 0))
        if not from_id or not to_num:
            return jsonify({"error": "from_account_id and to_account_number required"}), 400
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
        from_acc = Account.query.filter_by(id=from_id, user_id=uid).first()
        if not from_acc:
            return jsonify({"error": "Source account not found"}), 404
        to_acc = Account.query.filter_by(account_number=to_num).first()
        if not to_acc:
            return jsonify({"error": "Destination account not found"}), 404
        if from_acc.id == to_acc.id:
            return jsonify({"error": "Cannot transfer to the same account"}), 400
        if float(from_acc.balance) < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        from_acc.balance = float(from_acc.balance) - amount
        to_acc.balance   = float(to_acc.balance) + amount
        db.session.add(Transaction(account_id=from_acc.id, type="transfer", amount=amount,
                                   description="Transfer out",
                                   reference_account=to_acc.account_number))
        db.session.add(Transaction(account_id=to_acc.id, type="transfer", amount=amount,
                                   description="Transfer in",
                                   reference_account=from_acc.account_number))
        db.session.commit()
        return jsonify({"message": "Transfer successful", "balance": float(from_acc.balance)})

    return app


# ── Entry point ─────────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=False)
