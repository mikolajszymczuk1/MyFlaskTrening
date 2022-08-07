import unittest
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self) -> None:
        u = User(password='test')  # type: ignore
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self) -> None:
        u = User(password='test')  # type: ignore
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self) -> None:
        u = User(password='test')  # type: ignore
        self.assertTrue(u.verify_password('test'))
        self.assertFalse(u.verify_password('te'))

    def test_password_salts_are_random(self) -> None:
        u = User(password='test')  # type: ignore
        u2 = User(password='test2')  # type: ignore
        self.assertTrue(u.password_hash != u2.password_hash)