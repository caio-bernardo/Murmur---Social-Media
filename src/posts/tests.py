from django.test import TestCase
from ninja.testing import TestClient
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from ninja_jwt.tokens import RefreshToken
from posts.models import Post
from posts.views import router

class PostsTest(TestCase):

    def setUp(self) -> None:
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='password123'
        )

        # Create some test posts
        Post.objects.create(content="User1's post 1", author=self.user1)
        Post.objects.create(content="User1's post 2", author=self.user1)
        Post.objects.create(content="User2's post 1", author=self.user2)

        # Create post from yesterday for time-based tests
        yesterday_post = Post.objects.create(content="Yesterday's post", author=self.user1)
        yesterday_post.created_at = datetime.now() - timedelta(days=1)
        yesterday_post.save()

        self.tclient = TestClient(router)

        # Get JWT token for authentication tests
        refresh = RefreshToken.for_user(self.user1)
        self.token_user1 = str(refresh.access_token) # type: ignore


        refresh = RefreshToken.for_user(self.user2)
        self.token_user2 = str(refresh.access_token) # type: ignore


    def test_create_new_post(self):
        # should have a logged user
        response = self.tclient.post(
            "/",
            json={"content": "This is a new test post"},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["content"], "This is a new test post")
        self.assertEqual(response.json()["author"], self.user1.pk)

    def test_should_fail_create_post_without_auth(self):
        # Try to create without user authenticated
        response = self.tclient.post(
            "/",
            json={"content": "This post should not be created"}
        )
        self.assertEqual(response.status_code, 401)

    def test_should_fail_create_empty_post(self):
        # Try to create a post with empty string
        response = self.tclient.post(
            "/",
            json={"content": ""},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 422, response.json())  # Validation error

    def test_should_fail_create_oversized_post(self):
        # Try to create a post with over 280 characters
        oversized_content = "x" * 281
        response = self.tclient.post(
            "/",
            json={"content": oversized_content},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_get_a_single_post_of_otheruser(self):
        # Get a post from user2 while authenticated as user1
        post = Post.objects.filter(author=self.user2).first()
        assert post
        response = self.tclient.get(
            f"/{post.pk}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 200)
        # Should return a PostPublic schema (basic info)
        self.assertEqual(response.json()["content"], post.content)
        self.assertEqual(response.json()["author"], self.user2.pk)

    def test_get_a_single_post_of_yourown(self):
        # Get a post from user1 while authenticated as user1
        post = Post.objects.filter(author=self.user1).first()
        assert post
        response = self.tclient.get(
            f"/{post.pk}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 200)
        # Should return a PostPrivate schema (more detailed info)
        self.assertEqual(response.json()["content"], post.content)
        self.assertEqual(response.json()["author"], self.user1.pk)

    def test_get_post_by_user(self):
        # filter post by different users
        user1_posts_count = Post.objects.filter(author=self.user1).count()

        response = self.tclient.get(
            f"/?author={self.user1.pk}"
        )
        self.assertEqual(response.status_code, 200)
        # Check that we only get posts from user1
        self.assertEqual(len(response.json()["items"]), user1_posts_count, response.json())
        for post in response.json()['items']:
            self.assertEqual(post["author"], self.user1.pk)

    def test_get_post_by_time(self):
        # Filter post by last day
        filter_time = datetime.now() - timedelta(hours=12)
        recent_posts_count = Post.objects.filter(
            created_at__gte=filter_time
        ).count()

        response = self.tclient.get(
            f"/?created_after={filter_time}"
        )
        self.assertEqual(response.status_code, 200, response.json())
        # Should not include the post from yesterday
        self.assertEqual(len(response.json()["items"]), recent_posts_count)
        for post in response.json()["items"]:
            # Check that none of the returned posts has the content "Yesterday's post"
            self.assertNotEqual(post["content"], "Yesterday's post")

    def test_get_post_with_pagination(self):
        # Query with pagination
        response = self.tclient.get(
            "/?limit=2&offset=0"
        )
        self.assertEqual(response.status_code, 200)
        # Should return exactly 2 posts
        self.assertEqual(len(response.json()), 2)

        # Get the next page
        response = self.tclient.get(
            "/?limit=2&offset=2"
        )
        self.assertEqual(response.status_code, 200)
        # Should have less than or equal to 2 posts
        self.assertLessEqual(len(response.json()), 2)

        # Make sure pagination works correctly
        total_posts = Post.objects.count()
        all_posts = []

        # Get all posts through pagination
        for offset in range(0, total_posts, 2):
            response = self.tclient.get(f"/?limit=2&offset={offset}")
            all_posts.extend(response.json())

        # We should have retrieved all posts
        self.assertEqual(len(all_posts), total_posts)

    def test_delete_post(self):
        # Delete a post
        post = Post.objects.filter(author=self.user1).first()
        assert post
        post_id = post.pk

        response = self.tclient.delete(
            f"/{post_id}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 205)

        # Verify the post is really deleted
        self.assertFalse(Post.objects.filter(id=post_id).exists())

    def test_cannot_delete_other_users_post(self):
        # Try to delete a post from another user
        post = Post.objects.filter(author=self.user2).first()
        assert post
        post_id = post.pk

        response = self.tclient.delete(
            f"/{post_id}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify the post still exists
        self.assertTrue(Post.objects.filter(id=post_id).exists())
