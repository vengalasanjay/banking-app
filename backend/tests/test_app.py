import pytest
from app import create_app, db


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
        "JWT_ACCESS_TOKEN_EXPIRES": False,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, username="alice"):
    return client.post("/api/auth/register", json={
        "username": username, "email": f"{username}@test.com",
        "password": "pass1234", "full_name": f"{username.title()} Test",
    })

def _token(client, username="alice"):
    return _register(client, username).get_json()["token"]

def _hdr(token):
    return {"Authorization": f"Bearer {token}"}

def _acc_id(client, token):
    return client.get("/api/accounts", headers=_hdr(token)).get_json()[0]["id"]


# Health
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


# Register
def test_register_success(client):
    r = _register(client)
    assert r.status_code == 201
    assert "token" in r.get_json()

def test_register_duplicate_username(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 409

def test_register_missing_field(client):
    r = client.post("/api/auth/register", json={"username": "bob"})
    assert r.status_code == 400


# Login
def test_login_success(client):
    _register(client)
    r = client.post("/api/auth/login", json={"username": "alice", "password": "pass1234"})
    assert r.status_code == 200
    assert "token" in r.get_json()

def test_login_wrong_password(client):
    _register(client)
    r = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert r.status_code == 401

def test_login_unknown_user(client):
    r = client.post("/api/auth/login", json={"username": "ghost", "password": "x"})
    assert r.status_code == 401


# Accounts
def test_list_accounts(client):
    token = _token(client)
    r = client.get("/api/accounts", headers=_hdr(token))
    assert r.status_code == 200
    accs = r.get_json()
    assert len(accs) == 1
    assert accs[0]["account_type"] == "savings"
    assert accs[0]["balance"] == 0.0

def test_create_checking_account(client):
    token = _token(client)
    r = client.post("/api/accounts", json={"account_type": "checking"}, headers=_hdr(token))
    assert r.status_code == 201
    assert r.get_json()["account_type"] == "checking"

def test_create_invalid_account_type(client):
    token = _token(client)
    r = client.post("/api/accounts", json={"account_type": "crypto"}, headers=_hdr(token))
    assert r.status_code == 400


# Deposit
def test_deposit(client):
    token  = _token(client)
    acc_id = _acc_id(client, token)
    r = client.post(f"/api/accounts/{acc_id}/deposit",
                    json={"amount": 1000}, headers=_hdr(token))
    assert r.status_code == 200
    assert r.get_json()["balance"] == 1000.0

def test_deposit_negative(client):
    token  = _token(client)
    acc_id = _acc_id(client, token)
    r = client.post(f"/api/accounts/{acc_id}/deposit",
                    json={"amount": -50}, headers=_hdr(token))
    assert r.status_code == 400


# Withdraw
def test_withdraw_success(client):
    token  = _token(client)
    acc_id = _acc_id(client, token)
    client.post(f"/api/accounts/{acc_id}/deposit",
                json={"amount": 500}, headers=_hdr(token))
    r = client.post(f"/api/accounts/{acc_id}/withdraw",
                    json={"amount": 200}, headers=_hdr(token))
    assert r.status_code == 200
    assert r.get_json()["balance"] == 300.0

def test_withdraw_insufficient(client):
    token  = _token(client)
    acc_id = _acc_id(client, token)
    r = client.post(f"/api/accounts/{acc_id}/withdraw",
                    json={"amount": 9999}, headers=_hdr(token))
    assert r.status_code == 400


# Transfer
def test_transfer(client):
    t1 = _token(client, "alice")
    t2 = _token(client, "bob")
    a1 = _acc_id(client, t1)
    bob_num = client.get("/api/accounts", headers=_hdr(t2)).get_json()[0]["account_number"]
    client.post(f"/api/accounts/{a1}/deposit",
                json={"amount": 1000}, headers=_hdr(t1))
    r = client.post("/api/transfer",
                    json={"from_account_id": a1, "to_account_number": bob_num, "amount": 300},
                    headers=_hdr(t1))
    assert r.status_code == 200
    assert r.get_json()["balance"] == 700.0

def test_transfer_to_nonexistent(client):
    token  = _token(client)
    acc_id = _acc_id(client, token)
    client.post(f"/api/accounts/{acc_id}/deposit",
                json={"amount": 500}, headers=_hdr(token))
    r = client.post("/api/transfer",
                    json={"from_account_id": acc_id,
                          "to_account_number": "ACC9999999999", "amount": 100},
                    headers=_hdr(token))
    assert r.status_code == 404


# Transactions
def test_transactions_list(client):
    token  = _token(client)
    acc_id = _acc_id(client, token)
    client.post(f"/api/accounts/{acc_id}/deposit",
                json={"amount": 500, "description": "Salary"}, headers=_hdr(token))
    client.post(f"/api/accounts/{acc_id}/withdraw",
                json={"amount": 100, "description": "Groceries"}, headers=_hdr(token))
    r = client.get(f"/api/accounts/{acc_id}/transactions", headers=_hdr(token))
    assert r.status_code == 200
    txs = r.get_json()
    assert len(txs) == 2
    types = [t["type"] for t in txs]
    assert "deposit" in types
    assert "withdrawal" in types
