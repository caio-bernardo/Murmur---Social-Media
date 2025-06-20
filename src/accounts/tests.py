from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.testing import TestAsyncClient
from django.test import TestCase
from ninja.testing.client import NinjaResponse
from ninja_jwt.tokens import RefreshToken

from .views import router

class AccountsTest(TestCase):

    def setUp(self) -> None:
        self.tclient = TestAsyncClient(router)

    async def test_register_user(self):
        payload = {
            "username": "tester",
            "email": "tester@email.com",
            "password": "12345678",
            "password_confirm": "12345678",
            "first_name": "tester",
            "last_name": "clienter"
        }

        res = await self.tclient.post("/register", json=payload) # type: ignore
        self.assertEqual(res.status_code, 201, res.json())
        self.assertEqual(res.data['user']["username"], payload['username'])
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    async def test_username_already_inuse(self):
        same = "tester"
        await User.objects.acreate_user(
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
        res = await self.tclient.post("/register", json=payload)# type: ignore
        self.assertEqual(res.status_code, 409, res.json())

    async def test_password_dont_match(self):
        payload = {
            "username": "tester",
            "email": "tester@email.com",
            "password": "12345678",
            "password_confirm": "87654321",
            "first_name": "tester",
            "last_name": "clienter"
        }
        res = await self.tclient.post("/register", json=payload)# type: ignore
        self.assertEqual(res.status_code, 422, res.json())

    async def test_get_own_profile(self):

        user = await User.objects.acreate_user(
            username="tester",
        )
        refresh = RefreshToken.for_user(user)
        res = await self.tclient.get("/me", headers={"Authorization": "Bearer " + str(refresh.access_token)}) # type: ignore
        self.assertEqual(res.status_code, 200, res.json())
        self.assertIn("profile", res.data)

    async def test_unauthorized_access_to_profile(self):
        res = await self.tclient.get("/me")# type: ignore
        self.assertEqual(res.status_code, 401, res.json())
        self.assertEqual(res.json(), {"detail": "Unauthorized"}, res.json())


    async def test_invalid_token(self):
        token = "A194892bacddfe92199ecadfe001001294581"
        res = await self.tclient.get("/me", headers={"Authorization": "Bearer " + token}) #type: ignore
        self.assertEqual(res.status_code, 401, res.json())


    async def test_get_public_user(self):
        # Create a user that we'll look up
        user = await User.objects.acreate_user(
            username="public_test_user",
            first_name="Public",
            last_name="User"
        )
        # Hit GET /{username}
        res = await self.tclient.get(f"/{user.username}") # type: ignore
        self.assertEqual(res.status_code, 200, res.json())
        self.assertEqual(res.data["username"], user.username)
        self.assertIn("profile", res.data)


    async def test_update_own_profile(self):
        # Create a user and log in
        user = await User.objects.acreate_user(
            username="updater",
            password="123456",
            first_name="First",
            last_name="Initial"
        )
        refresh = RefreshToken.for_user(user)

        # Send patch request
        patch_data = {"first_name": "ChangedViaPatch"}
        res = await self.tclient.patch(
            "/me",
            headers={"Authorization": f"Bearer {refresh.access_token}"}, #type: ignore
            json=patch_data
        )
        # Depending on your intended design, 200 or 204 might be appropriate
        self.assertIn(res.status_code, [200, 204], res.json())

    async def test_delete_user_account(self):
        # Create a user and log in
        user = await User.objects.acreate_user(
            username="deleter",
            password="123456"
        )
        refresh = RefreshToken.for_user(user)

        # Send delete request
        res = await self.tclient.delete(
            "/me",
            headers={"Authorization": f"Bearer {refresh.access_token}"}# type: ignore
        )# type: ignore

        # Expect user deletion – you might choose 204 or 200 as well
        self.assertEqual(res.status_code, 204)

        # Confirm user has been removed from the database
        user_exists = await User.objects.filter(username="deleter").aexists()
        self.assertFalse(user_exists, "User was not successfully deleted")

    async def test_upload_user_photo(self):
        from io import BytesIO
        user = await User.objects.acreate_user(username="photo_tester", password="12345678")
        refresh = RefreshToken.for_user(user)

        fake_image = BytesIO(b"fakejpegdata")
        res = await self.tclient.post(
            "/me/photo",
            headers={"Authorization": f"Bearer {refresh.access_token}"},# type: ignore
            FILES={"file": SimpleUploadedFile("test_image.jpg", fake_image.getvalue(), "image/jpeg")}
        ) # type: ignore
        self.assertEqual(res.status_code, 205)

        # Confirm photo has been uploaded
        user = await User.objects.select_related("profile").aget(username="photo_tester")
        self.assertIsNotNone(user.profile.photo) # type: ignore

        await sync_to_async(user.profile.photo.delete)() # type: ignore

    async def test_delete_user_photo(self):
        user = await User.objects.acreate_user(username="photo_deleter", password="12345678")
        refresh = RefreshToken.for_user(user)

        res: NinjaResponse = await self.tclient.delete(
            "/me/photo",
            headers={"Authorization": f"Bearer {refresh.access_token}"}, #type: ignore
        )
        self.assertEqual(res.status_code, 204)
