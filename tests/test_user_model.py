import unittest
from app.models import User
from itsdangerous.url_safe import URLSafeSerializer
from app import create_app, db


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self) -> None:
        u = User(password='test')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self) -> None:
        u = User(password='test')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self) -> None:
        u = User(password='test')
        self.assertTrue(u.verify_password('test'))
        self.assertFalse(u.verify_password('te'))

    def test_password_salts_are_random(self) -> None:
        u = User(password='test')
        u2 = User(password='test2')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self) -> None:
        u = User(password='test')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self) -> None:
        u1 = User(password='test')
        u2 = User(password='test2')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_valid_change_email_token(self) -> None:
        u = User(email='test@gmail.com', password='test')
        db.session.add(u)
        db.session.commit()
        token = u.generate_change_email_token('new-test@gmail.com')
        self.assertTrue(u.confirm(token))
        self.assertEqual(u.email, 'new-test@gmail.com')

    def test_invalid_change_email_token(self) -> None:
        u1 = User(email='test1@gmail.com', password='test')
        u2 = User(email='test2@gmail.com', password='test2')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_change_email_token('new-test1@gmail.com')
        self.assertFalse(u2.confirm(token))
        self.assertEqual(u1.email, 'test1@gmail.com')
        self.assertEqual(u2.email, 'test2@gmail.com')
