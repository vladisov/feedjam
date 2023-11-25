import axios from "axios";
import Link from "next/link";
import { format } from "date-fns";

const SubscriptionItem = ({ subscription }) => (
  <div className="bg-white rounded-md p-6 mb-4 shadow">
    <p className="font-semibold">Subscription ID: {subscription.id}</p>
    <p className="font-semibold">Source ID: {subscription.source_id}</p>
    <p className="text-sm text-gray-500 mb-2">
      Created at: {format(new Date(subscription.created_at), "MM/dd/yyyy")}
    </p>
    <p>
      Last run:{" "}
      {subscription.last_run
        ? format(new Date(subscription.last_run), "MM/dd/yyyy")
        : "No runs yet"}
    </p>
    <Link
      href={`/runs/${subscription.id}`}
      className="text-indigo-500 hover:text-indigo-700"
    >
      View Runs
    </Link>
  </div>
);

const Subscriptions = ({ subscriptions }) => (
  <div className="max-w-2xl mx-auto px-4">
    <h1 className="text-3xl font-bold mb-6">Your Subscriptions</h1>
    {subscriptions.map((subscription) => (
      <SubscriptionItem key={subscription.id} subscription={subscription} />
    ))}
  </div>
);

export async function getServerSideProps(context) {
  const user_id = 1;

  const res = await axios.get(
    `http://localhost:8004/subscriptions?user_id=${user_id}`
  );
  const subscriptions = res.data;

  return {
    props: {
      subscriptions,
    },
  };
}

export default Subscriptions;
