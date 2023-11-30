import axios from "axios";
import Link from "next/link";
import { format } from "date-fns";
import { getSubscriptions } from "../utils";

const SubscriptionItem = ({ subscription }: { subscription: any }) => (
  <div className="border-2 border-black rounded-sm p-6 mb-4">
    <p className="font-semibold">Subscription ID: {subscription.id}</p>
    <p className="font-semibold">Source: {subscription.source_name}</p>
    <p className="text-sm text-gray-500 mb-2">
      Created at: {format(new Date(subscription.created_at), "MM/dd/yyyy")}
    </p>
  </div>
);

const Subscriptions = async () => {
  const subscriptions = await getSubscriptions(1);

  return (
    <div className="max-w-2xl mx-auto px-4 my-10 font-nunito">
      <h1 className="text-3xl font-bold mb-6">Your Subscriptions</h1>
      {subscriptions.map((subscription: any) => (
        <SubscriptionItem key={subscription.id} subscription={subscription} />
      ))}
    </div>
  );
};

// export async function getServerSideProps(context) {
//   const user_id = 1;

//   const res = await axios.get(
//     `http://localhost:8004/subscriptions?user_id=${user_id}`
//   );
//   const subscriptions = res.data;

//   return {
//     props: {
//       subscriptions,
//     },
//   };
// }

export default Subscriptions;
