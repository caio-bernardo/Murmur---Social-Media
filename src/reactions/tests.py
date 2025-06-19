from django.test import TestCase
from ninja.testing import TestClient
from django.contrib.auth.models import User

from ninja_jwt.tokens import RefreshToken
from posts.models import Post
from reactions.models import Reaction, ReactionType
from reactions.views import router


class ReactionsTest(TestCase):

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
        self.post2 = Post.objects.create(content="Another test post", author=self.user2)

        # Create some test reactions
        self.reaction1 = Reaction.objects.create(
            user=self.user1,
            post=self.post2,
            reaction_type=ReactionType.LIKE
        )

        self.reaction2 = Reaction.objects.create(
            user=self.user2,
            post=self.post,
            reaction_type=ReactionType.DISLIKE
        )

        self.tclient = TestClient(router)

        # Get JWT token for authentication tests
        refresh = RefreshToken.for_user(self.user1)
        self.token_user1 = str(refresh.access_token)  # type: ignore

        refresh = RefreshToken.for_user(self.user2)
        self.token_user2 = str(refresh.access_token)  # type: ignore

    def test_create_new_reaction(self):
        # Create a like reaction
        response = self.tclient.post(
            "/",
            json={"post_id": self.post.pk, "reaction_type": ReactionType.LIKE},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["reaction_type"], ReactionType.LIKE)
        self.assertEqual(response.json()["user"], self.user1.pk)
        self.assertEqual(response.json()["post"], self.post.pk)

    def test_update_existing_reaction(self):
        # First check the existing reaction
        existing_reaction = Reaction.objects.get(user=self.user1, post=self.post2)
        self.assertEqual(existing_reaction.reaction_type, ReactionType.LIKE)

        # Update it to a dislike
        response = self.tclient.post(
            "/",
            json={"post_id": self.post2.pk, "reaction_type": ReactionType.DISLIKE},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["reaction_type"], ReactionType.DISLIKE)

        # Verify in the database
        updated_reaction = Reaction.objects.get(user=self.user1, post=self.post2)
        self.assertEqual(updated_reaction.reaction_type, ReactionType.DISLIKE)

    def test_should_fail_create_reaction_without_auth(self):
        # Try to create without user authenticated
        response = self.tclient.post(
            "/",
            json={"post_id": self.post.pk, "reaction_type": ReactionType.LIKE}
        )
        self.assertEqual(response.status_code, 401)

    def test_should_fail_create_invalid_reaction_type(self):
        # Try to create with invalid reaction type
        response = self.tclient.post(
            "/",
            json={"post_id": self.post.pk, "reaction_type": "invalid_type"},
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 422)

    def test_delete_reaction(self):
        # Delete user1's reaction to post2
        response = self.tclient.delete(
            f"/{self.post2.pk}",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 204)

        # Verify the reaction is deleted
        self.assertFalse(Reaction.objects.filter(user=self.user1, post=self.post2).exists())

    def test_get_reaction_counts(self):
        # Add more reactions to have interesting counts
        Reaction.objects.create(
            user=self.user1,
            post=self.post,
            reaction_type=ReactionType.LIKE
        )

        # Get counts for post1
        response = self.tclient.get(f"/posts/{self.post.pk}/count")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["post_id"], self.post.pk)
        self.assertEqual(response.json()["likes"], 1)  # user1's like
        self.assertEqual(response.json()["dislikes"], 1)  # user2's dislike

    def test_get_user_reaction(self):
        # Get user2's reaction to post1
        response = self.tclient.get(
            f"/posts/{self.post.pk}/my-reaction",
            headers={"Authorization": f"Bearer {self.token_user2}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"], self.user2.pk)
        self.assertEqual(response.json()["post"], self.post.pk)
        self.assertEqual(response.json()["reaction_type"], ReactionType.DISLIKE)

    def test_get_nonexistent_user_reaction(self):
        # Try to get a reaction that doesn't exist
        response = self.tclient.get(
            f"/posts/{self.post.pk}/my-reaction",
            headers={"Authorization": f"Bearer {self.token_user1}"}
        )
        self.assertEqual(response.status_code, 404, response.json())  # Not found

    def test_get_reactions_with_filters(self):
        # Get all likes
        response = self.tclient.get("/?reaction_type=like")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(response.json()["items"][0]["reaction_type"], ReactionType.LIKE)

        # Get all reactions for post1
        response = self.tclient.get(f"/?post={self.post.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(response.json()["items"][0]["post"], self.post.pk)

        # Get all reactions by user1
        response = self.tclient.get(f"/?user={self.user1.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(response.json()["items"][0]["user"], self.user1.pk)
