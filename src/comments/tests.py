from django.test import TestCase
from ninja.testing import TestClient
from django.contrib.auth.models import User


from ninja_jwt.tokens import RefreshToken
from posts.models import Post
from comments.models import Comment
from comments.views import router


class CommentsTest(TestCase):

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

        # Create a test post
        self.post = Post.objects.create(content="Test post", author=self.user1)

        # Create some test comments
        self.comment1 = Comment.objects.create(
            content="User1's comment 1", post=self.post, author=self.user1
        )
        self.comment2 = Comment.objects.create(
            content="User2's comment 1", post=self.post, author=self.user2
        )

        self.tclient = TestClient(router)

        # Get JWT token for authentication tests
        refresh = RefreshToken.for_user(self.user1)
        self.token_user1 = str(refresh.access_token)  # type: ignore

        refresh = RefreshToken.for_user(self.user2)
        self.token_user2 = str(refresh.access_token)  # type: ignore

    def test_create_new_comment(self):
        # Create a new comment
        response = self.tclient.post(
            "/",
            json={"content": "This is a new test comment", "post_id": self.post.pk},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["content"], "This is a new test comment")
        self.assertEqual(response.json()["author"], self.user1.pk)

    def test_should_fail_create_comment_without_auth(self):
        # Try to create a comment without authentication
        response = self.tclient.post(
            "/",
            json={"content": "This comment should not be created", "post_id": self.post.pk}
        )
        self.assertEqual(response.status_code, 401)

    def test_should_fail_create_empty_comment(self):
        # Try to create a comment with an empty string
        response = self.tclient.post(
            "/",
            json={"content": "", "post_id": self.post.pk},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 422, response.json())  # Validation error

    def test_get_list_of_comments(self):
        # Get all comments for a post
        response = self.tclient.get(
            f"/?post_id={self.post.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)  # Two comments exist
        self.assertEqual(response.json()["items"][0]["content"], self.comment1.content)
        self.assertEqual(response.json()["items"][1]["content"], self.comment2.content)

    def test_get_a_single_comment(self):
        # Get a single comment
        response = self.tclient.get(
            f"/{self.comment1.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], self.comment1.content)
        self.assertEqual(response.json()["author"], self.user1.pk)

    def test_delete_comment(self):
        # Delete a comment
        response = self.tclient.delete(
            f"/{self.comment1.pk}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 205)

        # Verify the comment is really deleted
        self.assertFalse(Comment.objects.filter(id=self.comment1.pk).exists())

    def test_cannot_delete_other_users_comment(self):
        # Try to delete a comment from another user
        response = self.tclient.delete(
            f"/{self.comment2.pk}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify the comment still exists
        self.assertTrue(Comment.objects.filter(id=self.comment2.pk).exists())

    def test_get_comments_with_pagination(self):
        # Query with pagination
        response = self.tclient.get(
            f"/?post_id={self.post.pk}&limit=1&offset=0"
        )
        self.assertEqual(response.status_code, 200)
        # Should return exactly 1 comment
        self.assertEqual(len(response.json()["items"]), 1)

        # Get the next page
        response = self.tclient.get(
            f"/?post_id={self.post.pk}&limit=1&offset=1"
        )
        self.assertEqual(response.status_code, 200)
        # Should return the next comment
        self.assertEqual(len(response.json()["items"]), 1)

        # Make sure pagination works correctly
        total_comments = Comment.objects.filter(post=self.post).count()
        all_comments = []

        # Get all comments through pagination
        for offset in range(0, total_comments, 1):
            response = self.tclient.get(f"/?post_id={self.post.pk}&limit=1&offset={offset}")
            all_comments.extend(response.json()["items"])

        # We should have retrieved all comments
        self.assertEqual(len(all_comments), total_comments)
