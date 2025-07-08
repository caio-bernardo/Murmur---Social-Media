from django.test import TestCase
from ninja.testing import TestAsyncClient
from django.contrib.auth.models import User

from ninja_jwt.tokens import RefreshToken
from posts.models import Post
from reactions.models import Reaction, ReactionType
from reactions.apis import router


class ReactionsTest(TestCase):
    def setUp(self) -> None:
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="password123"
        )

        # Create a test post
        self.post = Post(content="Test post", author=self.user1)
        self.post.save()
        self.post2 = Post(content="Another test post", author=self.user2)
        self.post2.save()

        # Create some test reactions
        self.reaction1 = Reaction(
            user=self.user1, post=self.post2, reaction_type=ReactionType.LIKE
        )
        self.reaction1.save()

        self.reaction2 = Reaction(
            user=self.user2, post=self.post, reaction_type=ReactionType.DISLIKE
        )
        self.reaction2.save()

        self.tclient = TestAsyncClient(router)

        # Get JWT token for authentication tests
        refresh = RefreshToken.for_user(self.user1)
        self.token_user1 = str(refresh.access_token)  # type: ignore

        refresh = RefreshToken.for_user(self.user2)
        self.token_user2 = str(refresh.access_token)  # type: ignore

    async def test_create_new_reaction(self):
        # Create a like reaction
        response = await self.tclient.post(
            "/",
            json={"post_id": self.post.pk, "reaction_type": ReactionType.LIKE},
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["reaction_type"], ReactionType.LIKE)
        self.assertEqual(response.json()["user"], self.user1.pk)
        self.assertEqual(response.json()["post"], self.post.pk)

    async def test_update_existing_reaction(self):
        # First check the existing reaction
        existing_reaction = await Reaction.objects.filter(
            user=self.user1, post=self.post2
        ).afirst()
        assert existing_reaction
        self.assertEqual(existing_reaction.reaction_type, ReactionType.LIKE)

        # Update it to a dislike
        response = await self.tclient.post(
            "/",
            json={"post_id": self.post2.pk, "reaction_type": ReactionType.DISLIKE},
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["reaction_type"], ReactionType.DISLIKE)

        # Verify in the database
        updated_reaction = await Reaction.objects.filter(
            user=self.user1, post=self.post2
        ).afirst()
        assert updated_reaction
        self.assertEqual(updated_reaction.reaction_type, ReactionType.DISLIKE)

    async def test_should_fail_create_reaction_without_auth(self):
        # Try to create without user authenticated
        response = await self.tclient.post(
            "/", json={"post_id": self.post.pk, "reaction_type": ReactionType.LIKE}
        )  # type: ignore
        self.assertEqual(response.status_code, 401)

    async def test_should_fail_create_invalid_reaction_type(self):
        # Try to create with invalid reaction type
        response = await self.tclient.post(
            "/",
            json={"post_id": self.post.pk, "reaction_type": "invalid_type"},
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 422)

    async def test_delete_reaction(self):
        # Delete user1's reaction to post2
        response = await self.tclient.delete(
            f"/{self.post2.pk}", headers={"Authorization": f"Bearer {self.token_user1}"}
        )  # type: ignore
        self.assertEqual(response.status_code, 204)

        # Verify the reaction is deleted
        reaction_exists = await Reaction.objects.filter(
            user=self.user1, post=self.post2
        ).aexists()
        self.assertFalse(reaction_exists)

    async def test_get_reaction_counts(self):
        # Add more reactions to have interesting counts
        reaction = Reaction(
            user=self.user1, post=self.post, reaction_type=ReactionType.LIKE
        )
        await reaction.asave()

        # Get counts for post1
        response = await self.tclient.get(f"/posts/{self.post.pk}/count")  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["post_id"], self.post.pk)
        self.assertEqual(json_data["likes"], 1)  # user1's like
        self.assertEqual(json_data["dislikes"], 1)  # user2's dislike

    async def test_get_user_reaction(self):
        # Get user2's reaction to post1
        response = await self.tclient.get(
            f"/posts/{self.post.pk}/my-reaction",
            headers={"Authorization": f"Bearer {self.token_user2}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["user"], self.user2.pk)
        self.assertEqual(json_data["post"], self.post.pk)
        self.assertEqual(json_data["reaction_type"], ReactionType.DISLIKE)

    async def test_get_nonexistent_user_reaction(self):
        # Try to get a reaction that doesn't exist
        response = await self.tclient.get(
            f"/posts/{self.post.pk}/my-reaction",
            headers={"Authorization": f"Bearer {self.token_user1}"},
        )  # type: ignore
        self.assertEqual(response.status_code, 404)  # Not found

    async def test_get_reactions_with_filters(self):
        # Get all likes
        response = await self.tclient.get("/?reaction_type=like")  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["items"]), 1)
        self.assertEqual(json_data["items"][0]["reaction_type"], ReactionType.LIKE)

        # Get all reactions for post1
        response = await self.tclient.get(f"/?post={self.post.pk}")  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["items"]), 1)
        self.assertEqual(json_data["items"][0]["post"], self.post.pk)

        # Get all reactions by user1
        response = await self.tclient.get(f"/?user={self.user1.pk}")  # type: ignore
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["items"]), 1)
        self.assertEqual(json_data["items"][0]["user"], self.user1.pk)

        # Test pagination by getting all reactions
        total_reactions = await Reaction.objects.acount()
        all_reactions = []

        # Get all reactions through pagination
        for offset in range(0, total_reactions, 1):
            response = await self.tclient.get(f"/?limit=1&offset={offset}")  # type: ignore
            all_reactions.extend(response.json()["items"])

        # We should have retrieved all reactions
        self.assertEqual(len(all_reactions), total_reactions)
