
import pytest
from model.schema.feed_schema import SubscriptionSchema
from model.schema.user_schema import UserSchema
from tests.test_app import _create_user, client


def _create_subscription(user: UserSchema, resource_url: str):
    response = client.post(
        "/subscribe",
        json={
            "user_id": user.id,
            "resource_url": resource_url,
        },
    )
    return SubscriptionSchema(**response.json()["data"])


def test_create_subscription_with_new_source(cleanup):
    user = _create_user("yam")
    subscription = _create_subscription(user, "https://www.test.lalala/rss")

    assert subscription.source.resource_url == "https://www.test.lalala/rss"
    assert subscription.source.name == "https://www.test.lalala/rss"


def test_create_subscription_with_existing_source(cleanup):
    yam = _create_user("yam")
    opa = _create_user("opa")
    _create_subscription(yam, "https://www.test.lalala/rss")
    subscription = _create_subscription(opa, "https://www.test.lalala/rss")

    assert subscription.source_id == 1
    assert subscription.user_id == opa.id


@pytest.mark.parametrize("resource_url", [
    "https://www.test1.lalala/rss",
    "https://www.test2.lalala/rss",
    "https://www.test3.lalala/rss"
])
def test_get_subscriptions(cleanup, resource_url):
    # Create a couple of users and subscriptions
    user1 = _create_user("yam")
    user2 = _create_user("opa")
    subscription1 = _create_subscription(user1, resource_url)
    subscription2 = _create_subscription(user2, resource_url)

    # Get subscriptions for user1
    response = client.get(f"/subscriptions?user_id={user1.id}")
    subscriptions = response.json()

    # Verify the response status and the subscriptions
    assert response.status_code == 200
    assert len(subscriptions) == 1
    assert subscriptions[0]['id'] == subscription1.id
    assert subscriptions[0]['user_id'] == user1.id
    assert subscriptions[0]['source']['resource_url'] == resource_url
    assert subscriptions[0]['source']['name'] == resource_url

    # Get subscriptions for user2
    response = client.get(f"/subscriptions?user_id={user2.id}")
    subscriptions = response.json()

    # Verify the response status and the subscriptions
    assert response.status_code == 200
    assert len(subscriptions) == 1
    assert subscriptions[0]['id'] == subscription2.id
    assert subscriptions[0]['user_id'] == user2.id
    assert subscriptions[0]['source']['resource_url'] == resource_url
    assert subscriptions[0]['source']['name'] == resource_url
