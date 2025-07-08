from django.test import TestCase
from ninja.testing import TestAsyncClient
from django.contrib.auth.models import User

from murmur.api import app
from apps.posts.models import Post


class IntegratedAppTest(TestCase):
    """
    Integration test class that tests the complete user journey through the application.
    Tests a "happy path" where a user registers, views their profile, creates posts,
    comments on posts, and reacts to posts.
    """

    def setUp(self):
        # Create a test client for the entire API
        self.tclient = TestAsyncClient(app)

        # Create a second user for interaction tests
        self.other_user = User.objects.create_user(
            username="other_user",
            password="securepass123",
            email="other@example.com",
            first_name="Other",
            last_name="User",
        )

        # Create some content from the other user
        self.other_post = Post.objects.create(
            content="Post from other user", author=self.other_user
        )

    async def test_user_happy_path(self):
        """
        Test the complete user journey: registration, profile viewing,
        posting, commenting and reacting to posts.
        """
        # Step 1: Register a new user
        register_payload = {
            "username": "happyuser",
            "email": "happy@example.com",
            "password": "secure123",
            "password_confirm": "secure123",
            "first_name": "Happy",
            "last_name": "User",
        }

        register_response = await self.tclient.post(
            "/accounts/register", json=register_payload
        )  # type: ignore
        self.assertEqual(register_response.status_code, 201)

        # Extract tokens for authentication
        access_token = register_response.json()["access"]
        auth_header = {"Authorization": f"Bearer {access_token}"}

        # Step 2: View user profile
        profile_response = await self.tclient.get("/accounts/me", headers=auth_header)  # type: ignore
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["username"], "happyuser")

        # Step 3: Create a new post
        post_payload = {"content": "Hello world! This is my first post."}
        post_response = await self.tclient.post(
            "/posts/", json=post_payload, headers=auth_header
        )  # type: ignore
        self.assertEqual(post_response.status_code, 201)

        _ = post_response.json().get("id") or post_response.json().get("pk")

        # Step 4: Comment on the other user's post
        comment_payload = {
            "content": "Great post! I really enjoyed it.",
            "post_id": self.other_post.pk,
        }
        comment_response = await self.tclient.post(
            "/comments/", json=comment_payload, headers=auth_header
        )  # type: ignore
        self.assertEqual(comment_response.status_code, 201)

        # Step 5: Like the other user's post
        reaction_payload = {"post_id": self.other_post.pk, "reaction_type": "like"}
        reaction_response = await self.tclient.post(
            "/reactions/", json=reaction_payload, headers=auth_header
        )  # type: ignore
        self.assertEqual(reaction_response.status_code, 201)

        # Step 6: Verify the like count increased
        count_response = await self.tclient.get(
            f"/reactions/posts/{self.other_post.pk}/count"
        )  # type: ignore
        self.assertEqual(count_response.status_code, 200)
        self.assertEqual(count_response.json()["likes"], 1)

        # Step 7: Check feed includes both posts
        feed_response = await self.tclient.get("/posts/?limit=10", headers=auth_header)  # type: ignore
        self.assertEqual(feed_response.status_code, 200)
        self.assertGreaterEqual(len(feed_response.json()["items"]), 2)

        # Step 8: Retrieve comments for the other user's post
        comments_response = await self.tclient.get(
            f"/comments/?post_id={self.other_post.pk}"
        )  # type: ignore
        self.assertEqual(comments_response.status_code, 200)
        self.assertEqual(len(comments_response.json()["items"]), 1)
        self.assertEqual(
            comments_response.json()["items"][0]["content"],
            "Great post! I really enjoyed it.",
        )
