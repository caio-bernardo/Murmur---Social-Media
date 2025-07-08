from django.test import TestCase
from ninja.testing import TestAsyncClient
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from ninja_jwt.tokens import RefreshToken
from posts.models import Post
from posts.views import router


class PostsTest(TestCase):
    def setUp(self) -> None:
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="password123"
        )

        # Create some test posts
        post1 = Post(content="User1's post 1", author=self.user1)
        post1.save()
        post2 = Post(content="User1's post 2", author=self.user1)
        post2.save()
        post3 = Post(content="User2's post 1", author=self.user2)
        post3.save()

        # Create post from yesterday for time-based tests
        yesterday_post = Post(content="Yesterday's post", author=self.user1)
        yesterday_post.save()
        yesterday_post.created_at = datetime.now() - timedelta(days=1)
        yesterday_post.save()

        self.tclient = TestAsyncClient(router)

        # Get JWT token for authentication tests
        refresh = RefreshToken.for_user(self.user1)
        self.token_user1 = str(refresh.access_token)  # type: ignore

        refresh = RefreshToken.for_user(self.user2)
        self.token_user2 = str(refresh.access_token)  # type: ignore

    async def test_create_new_post(self):
        # should have a logged user
        response = await self.tclient.post(
            "/",
            json={"content": "This is a new test post"},
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 201)
        json_data = response.json()
        self.assertEqual(json_data["content"], "This is a new test post")
        self.assertEqual(json_data["author"], self.user1.pk)

    async def test_should_fail_create_post_without_auth(self):
        # Try to create without user authenticated
        response = await self.tclient.post(
            "/", json={"content": "This post should not be created"}
        )  # type: ignore
        self.assertEqual(response.status_code, 401)

    async def test_should_fail_create_empty_post(self):
        # Try to create a post with empty string
        response = await self.tclient.post(
            "/",
            json={"content": ""},
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 422)  # Validation error

    async def test_should_fail_create_oversized_post(self):
        # Try to create a post with over 280 characters
        oversized_content = "x" * 281
        response = await self.tclient.post(
            "/",
            json={"content": oversized_content},
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 422)  # Validation error

    async def test_get_a_single_post_of_otheruser(self):
        # Get a post from user2 while authenticated as user1
        post = await Post.objects.filter(author=self.user2).afirst()
        assert post
        response = await self.tclient.get(
            f"/{post.pk}", headers={"Authorization": f"Bearer {self.token_user1}"}
        )  # type: ignore
        self.assertEqual(response.status_code, 200)
        # Should return a PostPublic schema (basic info)
        json_data = response.json()
        self.assertEqual(json_data["content"], post.content)
        self.assertEqual(json_data["author"], self.user2.pk)

    async def test_get_a_single_post_of_yourown(self):
        # Get a post from user1 while authenticated as user1
        post = await Post.objects.filter(author=self.user1).afirst()
        assert post
        response = await self.tclient.get(
            f"/{post.pk}", headers={"Authorization": f"Bearer {self.token_user1}"}
        )  # type: ignore
        self.assertEqual(response.status_code, 200)
        # Should return a PostPrivate schema (more detailed info)
        json_data = response.json()
        self.assertEqual(json_data["content"], post.content)
        self.assertEqual(json_data["author"], self.user1.pk)

    async def test_get_post_by_user(self):
        # filter post by different users
        user1_posts_count = await Post.objects.filter(author=self.user1).acount()

        response = await self.tclient.get(f"/?author={self.user1.pk}")  # type: ignore
        self.assertEqual(response.status_code, 200)
        # Check that we only get posts from user1
        json_data = response.json()
        self.assertEqual(len(json_data["items"]), user1_posts_count)
        for post in json_data["items"]:
            self.assertEqual(post["author"], self.user1.pk)

    async def test_get_post_by_time(self):
        # Filter post by last day
        filter_time = datetime.now() - timedelta(hours=12)
        recent_posts_count = await Post.objects.filter(
            created_at__gte=filter_time
        ).acount()

        response = await self.tclient.get(f"/?created_after={filter_time.isoformat()}")  # type: ignore
        self.assertEqual(response.status_code, 200)
        # Should not include the post from yesterday
        json_data = response.json()
        self.assertEqual(len(json_data["items"]), recent_posts_count)
        for post in json_data["items"]:
            # Check that none of the returned posts has the content "Yesterday's post"
            self.assertNotEqual(post["content"], "Yesterday's post")

    async def test_get_post_with_pagination(self):
        # Query with pagination
        response = await self.tclient.get("/?limit=2&offset=0")  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        # Should return exactly 2 posts
        self.assertEqual(len(json_data["items"]), 2)

        # Get the next page
        response = await self.tclient.get("/?limit=2&offset=2")  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        # Should have less than or equal to 2 posts
        self.assertLessEqual(len(json_data["items"]), 2)

        # Make sure pagination works correctly
        total_posts = await Post.objects.acount()
        all_posts = []

        # Get all posts through pagination
        for offset in range(0, total_posts, 2):
            response = await self.tclient.get(f"/?limit=2&offset={offset}")  # type: ignore
            json_data = response.json()
            all_posts.extend(json_data["items"])

        # We should have retrieved all posts
        self.assertEqual(len(all_posts), total_posts)

    async def test_delete_post(self):
        # Delete a post
        post = await Post.objects.filter(author=self.user1).afirst()
        assert post
        post_id = post.pk

        response = await self.tclient.delete(
            f"/{post_id}", headers={"Authorization": f"Bearer {self.token_user1}"}
        )  # type: ignore
        self.assertEqual(response.status_code, 205)

        # Verify the post is really deleted
        post_exists = await Post.objects.filter(id=post_id).aexists()
        self.assertFalse(post_exists)

    async def test_cannot_delete_other_users_post(self):
        # Try to delete a post from another user
        post = await Post.objects.filter(author=self.user2).afirst()
        assert post
        post_id = post.pk

        response = await self.tclient.delete(
            f"/{post_id}", headers={"Authorization": f"Bearer {self.token_user1}"}
        )  # type: ignore
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify the post still exists
        post_exists = await Post.objects.filter(id=post_id).aexists()
        self.assertTrue(post_exists)
