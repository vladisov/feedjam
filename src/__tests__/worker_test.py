from unittest.mock import MagicMock, Mock, patch
import pytest
from model.schema.feed_schema import SubscriptionUpdate
from tasks.worker import generic_job_runner


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def run_storage_mock():
    run_storage = MagicMock()
    run_storage.get_all_pending_runs.return_value = [
        MagicMock(job_type='all_subscriptions', id=1),
        MagicMock(job_type='single_subscription', id=2, subscription_id=10),
        MagicMock(job_type='all_user_views', id=3),
        MagicMock(job_type='single_user_view', id=4, user_id=11),
    ]
    return run_storage


@patch("tasks.worker.schedule_all_subs.delay")
@patch("tasks.worker.subscription_run.delay")
@patch("tasks.worker.generate_all_views.delay")
@patch("tasks.worker.generate_single_user_view.delay")
def test_generic_job_runner(
    mock_generate_single_user_view, mock_generate_all_views,
    mock_subscription_run, mock_schedule_all_subs,
    run_storage_mock, mock_db_session
):
    with patch("tasks.worker.RunStorage", return_value=run_storage_mock):
        with patch("tasks.worker.get_db", return_value=iter([mock_db_session])):
            res = generic_job_runner()
            assert res is True

    mock_schedule_all_subs.assert_called_once_with(1)
    mock_subscription_run.assert_called_once_with(2, 10)
    mock_generate_all_views.assert_called_once_with(3)
    mock_generate_single_user_view.assert_called_once_with(4, 11)

# @patch("tasks.worker.FeedStorage")
# @patch("tasks.worker.SubscriptionStorage")
# @patch("tasks.worker.FeedService")
# @patch("tasks.worker.RunStorage")
# @patch("tasks.worker.SourceStorage")
# @patch("tasks.worker.DataExtractor")
# def test_do_run(mock_data_extractor,
#                 mock_source_storage,
#                 mock_run_storage,
#                 mock_feed_service,
#                 mock_subscription_storage,
#                 mock_feed_storage,
#                 mock_db_session):
#     mock_run = Mock(id=1, subscription_id=2)
#     mock_run_storage.return_value.get_run.return_value = mock_run

#     with patch("tasks.worker.get_db", return_value=iter([mock_db_session])):
#         do_run(1)

#     mock_run_storage.assert_called_once_with(mock_db_session)
#     mock_run_storage.return_value.get_run.assert_called_once_with(1)
#     mock_run_storage.return_value.update_run_status.assert_any_call(
#         1, "running")

#     mock_feed_service.assert_called_once_with(
#         mock_feed_storage.return_value,
#         mock_subscription_storage.return_value,
#         mock_source_storage.return_value,
#         mock_data_extractor.return_value)
#     mock_feed_service.return_value.fetch_and_save_feed_items.assert_called_once_with(
#         2)
#     mock_run_storage.return_value.update_run_status.assert_any_call(
#         1, "success")
#     assert mock_subscription_storage.return_value.update_subscription.call_count == 1
#     args, _ = mock_subscription_storage.return_value.update_subscription.call_args
#     assert args[1] == 2
#     assert isinstance(args[0], SubscriptionUpdate)
