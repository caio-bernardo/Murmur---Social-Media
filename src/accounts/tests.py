from django.contrib.auth.models import User
from ninja.testing import TestClient
from django.test import TestCase
from ninja_jwt.tokens import RefreshToken

from .views import router

class AccountsTest(TestCase):

    def setUp(self) -> None:
        self.tclient = TestClient(router)

    def test_register_user(self):
        payload = {
            "username": "tester",
            "email": "tester@email.com",
            "password": "12345678",
            "password_confirm": "12345678",
            "first_name": "tester",
            "last_name": "clienter"
        }

        res = self.tclient.post("/register", json=payload)
        self.assertEqual(res.status_code, 201, res.json())
        self.assertEqual(res.data['user']["username"], payload['username'])
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_username_already_inuse(self):
        same = "tester"
        User.objects.create_user(
            username=same
        )
        payload = {
                "username": same,
                "email": "tester@email.com",
                "password": "12345678",
                "password_confirm": "12345678",
                "first_name": "tester",
                "last_name": "clienter"
        }
        res = self.tclient.post("/register", json=payload)
        self.assertEqual(res.status_code, 409, res.json())

    def test_password_dont_match(self):
        payload = {
            "username": "tester",
            "email": "tester@email.com",
            "password": "12345678",
            "password_confirm": "87654321",
            "first_name": "tester",
            "last_name": "clienter"
        }
        res = self.tclient.post("/register", json=payload)
        self.assertEqual(res.status_code, 422, res.json())

    def test_get_own_profile(self):

        user = User.objects.create_user(
            username="tester",
        )
        refresh = RefreshToken.for_user(user)
        res = self.tclient.get("/me", headers={"Authorization": "Bearer " + str(refresh.access_token)})
        self.assertEqual(res.status_code, 200, res.json())
        self.assertIn("profile", res.data)

    def test_unauthorized_access_to_profile(self):
        res = self.tclient.get("/me")
        self.assertEqual(res.status_code, 401, res.json())
        self.assertEqual(res.json(), {"detail": "Unauthorized"}, res.json())


    def test_invalid_token(self):
        token = "A194892bacddfe92199ecadfe001001294581"
        res = self.tclient.get("/me", header={"Authorization": "Bearer" + token})
        self.assertEqual(res.status_code, 401, res.json())


    def test_get_public_user(self):
        # Create a user that we'll look up
        user = User.objects.create_user(
            username="public_test_user",
            first_name="Public",
            last_name="User"
        )
        # Hit GET /{username}
        res = self.tclient.get(f"/{user.username}")
        self.assertEqual(res.status_code, 200, res.json())
        self.assertEqual(res.data["username"], user.username)
        self.assertIn("profile", res.data)


    def test_update_own_profile(self):
        # Create a user and log in
        user = User.objects.create_user(
            username="updater",
            password="123456",
            first_name="First",
            last_name="Initial"
        )
        refresh = RefreshToken.for_user(user)

        # Send patch request
        patch_data = {"first_name": "ChangedViaPatch"}
        res = self.tclient.patch(
            "/me",
            headers={"Authorization": f"Bearer {refresh.access_token}"}, #type: ignore
            json=patch_data
        )
        # Depending on your intended design, 200 or 204 might be appropriate
        self.assertIn(res.status_code, [200, 204], res.json())

    def test_delete_user_account(self):
        # Create a user and log in
        user = User.objects.create_user(
            username="deleter",
            password="123456"
        )
        refresh = RefreshToken.for_user(user)

        # Send delete request
        res = self.tclient.delete(
            "/me",
            headers={"Authorization": f"Bearer {refresh.access_token}"} #type: ignore
        )

        # Expect user deletion – you might choose 204 or 200 as well
        self.assertEqual(res.status_code, 204)

        # Confirm user has been removed from the database
        user_exists = User.objects.filter(username="deleter").exists()
        self.assertFalse(user_exists, "User was not successfully deleted")
