from django.test import TestCase
from ninja.testing import TestAsyncClient
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

        self.tclient = TestAsyncClient(router)

        # Get JWT token for authentication tests
        refresh = RefreshToken.for_user(self.user1)
        self.token_user1 = str(refresh.access_token)  # type: ignore

        refresh = RefreshToken.for_user(self.user2)
        self.token_user2 = str(refresh.access_token)  # type: ignore

    async def test_create_new_comment(self):
        # Create a new comment
        response = await self.tclient.post(
            "/",
            json={"content": "This is a new test comment", "post_id": self.post.pk},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        ) #type: ignore
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["content"], "This is a new test comment")
        self.assertEqual(response.json()["author"], self.user1.pk)

    async def test_should_fail_create_comment_without_auth(self):
        # Try to create a comment without authentication
        response = await self.tclient.post(
            "/",
            json={"content": "This comment should not be created", "post_id": self.post.pk}
        ) #type: ignore
        self.assertEqual(response.status_code, 401)

    async def test_should_fail_create_empty_comment(self):
        # Try to create a comment with an empty string
        response = await self.tclient.post(
            "/",
            json={"content": "", "post_id": self.post.pk},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        ) #type: ignore
        self.assertEqual(response.status_code, 422)  # Validation error

    async def test_get_list_of_comments(self):
        # Get all comments for a post
        response = await self.tclient.get(
            f"/?post={self.post.pk}"
        ) #type: ignore
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)  # Two comments exist

        # Note: In async tests, the order might not be guaranteed
        contents = [item["content"] for item in response.json()["items"]]
        self.assertIn(self.comment1.content, contents)
        self.assertIn(self.comment2.content, contents)

    async def test_get_a_single_comment(self):
        # Get a single comment
        response = await self.tclient.get(
            f"/{self.comment1.pk}"
        ) #type: ignore
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["content"], self.comment1.content)
        self.assertEqual(response.json()["author"], self.user1.pk)

    async def test_delete_comment(self):
        # Delete a comment
        comment = await Comment.objects.filter(author=self.user1).afirst()
        assert comment
        comment_id = comment.pk

        response = await self.tclient.delete(
            f"/{comment_id}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        ) #type: ignore
        self.assertEqual(response.status_code, 205)

        # Verify the comment is really deleted
        comment_exists = await Comment.objects.filter(id=comment_id).aexists()
        self.assertFalse(comment_exists)

    async def test_cannot_delete_other_users_comment(self):
        # Try to delete a comment from another user
        comment = await Comment.objects.filter(author=self.user2).afirst()
        assert comment
        comment_id = comment.pk

        response = await self.tclient.delete(
            f"/{comment_id}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        ) #type: ignore
        self.assertEqual(response.status_code, 403, response.data)  # Forbidden

        # Verify the comment still exists
        comment_exists = await Comment.objects.filter(id=comment_id).aexists()
        self.assertTrue(comment_exists)

    async def test_get_comments_with_pagination(self):
        # Query with pagination
        response = await self.tclient.get(
            f"/?post={self.post.pk}&limit=1&offset=0"
        ) #type: ignore
        self.assertEqual(response.status_code, 200)
        # Should return exactly 1 comment
        self.assertEqual(len(response.json()["items"]), 1)

        # Get the next page
        response = await self.tclient.get(
            f"/?post={self.post.pk}&limit=1&offset=1"
        ) #type: ignore
        self.assertEqual(response.status_code, 200)
        # Should return the next comment
        self.assertEqual(len(response.json()["items"]), 1)

        # Make sure pagination works correctly
        total_comments = await Comment.objects.filter(post=self.post).acount()
        all_comments = []

        # Get all comments through pagination
        for offset in range(0, total_comments, 1):
            response = await self.tclient.get(f"/?post={self.post.pk}&limit=1&offset={offset}") #type: ignore
            all_comments.extend(response.json()["items"])

        # We should have retrieved all comments
        self.assertEqual(len(all_comments), total_comments)
