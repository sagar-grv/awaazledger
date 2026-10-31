"""Tests verifying that database seeding populates required users and transactions."""

from app.db.session import SessionLocal
from app.models.user import User
from app.models.transaction import Transaction


def test_seed_db_data_counts():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        assert len(users) >= 5
        names = [u.name for u in users]
        assert "Rohit Verma" in names
        assert "Priya Sharma" in names
        assert "Vikram Singh" in names
        assert "Amit Kumar" in names
        assert "Sunita Devi" in names

        txns = db.query(Transaction).all()
        assert len(txns) >= 8
        utrs = [t.utr for t in txns]
        assert "987654321012" in utrs  # SCN-01
        assert "998877665544" in utrs  # SCN-03
        assert "556677889900" in utrs  # Ghost success
        assert "778899001122" in utrs  # Duplicate leg 1
        assert "778899001123" in utrs  # Duplicate leg 2
    finally:
        db.close()
