import pytest
from unittest.mock import MagicMock, Mock, patch
from model.schema.feed_schema import SubscriptionUpdate
from tasks.worker import do_run, generate_user_view, schedule_run
from utils import config


@pytest.fixture
def mock_db_session():
    return Mock()


@patch("tasks.worker.do_run.delay")
@patch("tasks.worker.RunStorage")
@patch("tasks.worker.SubscriptionStorage")
def test_schedule_run(mock_subscription_storage, mock_run_storage, mock_do_run, mock_db_session):
    mock_subscriptions = [Mock(id=1), Mock(id=2)]
    mock_subscription_storage.return_value.get_subscriptions_to_run.return_value = mock_subscriptions
    mock_run_storage.return_value.create_run.return_value = Mock(id=1)

    with patch("tasks.worker.get_db", return_value=iter([mock_db_session])):
        schedule_run()

    mock_subscription_storage.assert_called_once_with(mock_db_session)
    mock_subscription_storage.return_value.get_subscriptions_to_run.assert_called_once()
    mock_run_storage.assert_called_once_with(mock_db_session)
    assert mock_do_run.call_count == 2


@patch("tasks.worker.FeedStorage")
@patch("tasks.worker.SubscriptionStorage")
@patch("tasks.worker.FeedService")
@patch("tasks.worker.RunStorage")
@patch("tasks.worker.DataExtractor")
def test_do_run(mock_data_extractor, mock_run_storage, mock_feed_service, mock_subscription_storage,
                mock_feed_storage, mock_db_session):
    mock_run = Mock(id=1, subscription_id=2)
    mock_run_storage.return_value.get_run.return_value = mock_run

    with patch("tasks.worker.get_db", return_value=iter([mock_db_session])):
        do_run(1)

    mock_run_storage.assert_called_once_with(mock_db_session)
    mock_run_storage.return_value.get_run.assert_called_once_with(1)
    mock_run_storage.return_value.update_run_status.assert_any_call(
        1, "running")
    mock_feed_service.assert_called_once_with(
        mock_feed_storage.return_value, mock_subscription_storage.return_value, mock_data_extractor.return_value)
    mock_feed_service.return_value.fetch_and_save_feed_items.assert_called_once_with(
        2)
    mock_run_storage.return_value.update_run_status.assert_any_call(
        1, "success")
    assert mock_subscription_storage.return_value.update_subscription.call_count == 1
    args, kwargs = mock_subscription_storage.return_value.update_subscription.call_args
    assert args[1] == 2
    assert isinstance(args[0], SubscriptionUpdate)
