import unittest, time
from app.models import User, AnonymousUser, Role, Permission, Follow
from app import create_app, db
from datetime import datetime


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

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

    def test_user_role(self):
        u = User(email='test@gmail.com', password='test')
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_moderator_role(self):
        r = Role.query.filter_by(name='Moderator').first()
        u = User(email='test@gmail.com', password='test', role=r)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_administrator_role(self):
        r = Role.query.filter_by(name='Administrator').first()
        u = User(email='test@gmail.com', password='test', role=r)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertTrue(u.can(Permission.ADMIN))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_timestamps(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(
            (datetime.now() - u.member_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.now() - u.last_seen).total_seconds() < 3)

    def test_ping(self):
        u = User(password='test')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_gravatar(self):
        u = User(email='test@gmail.com', password='test')
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')

        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatar_ssl = u.gravatar()
            self.assertTrue('http://secure.gravatar.com/avatar/' + '1aedb8d9dc4751e229a335e371db8058' in gravatar)
            self.assertTrue('s=256' in gravatar_256)
            self.assertTrue('r=pg' in gravatar_pg)
            self.assertTrue('d=retro' in gravatar_retro)
            self.assertTrue('https://secure.gravatar.com/avatar/' + '1aedb8d9dc4751e229a335e371db8058' in gravatar_ssl)

    def test_follows(self):
        u1 = User(email='john@gmail.com', password='test1')
        u2 = User(email='susan@gmail.com', password='test2')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        time.sleep(2)
        timestamp_after = datetime.now()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u2.followers.count() == 2)
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        self.assertTrue(f.timestamp <= timestamp_after)
        f = u2.followers.all()[-2]
        self.assertTrue(f.follower == u1)
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)
