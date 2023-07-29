import axios from "axios";
import { format } from "date-fns";
import FeedItem from "../components/feed/feed-item";
import Link from "next/link";
import { mockFeedData } from "../mocks/feed";

const Timeline = ({ feed }) => (
  <div className="font-serif max-w-5xl mx-auto">
    <nav className="p-6 mb-6 border rounded-md shadow-md">
      <Link href="/subscriptions" className="text-sky-500 hover:text-sky-700">
        Subscriptions
      </Link>
      <Link href="/runs" className="ml-6 text-sky-500 hover:text-sky-700">
        Runs
      </Link>{" "}
    </nav>
    <div className="flex flex-col">
      {feed.map((item) => (
        <FeedItem key={item.id} item={item} />
      ))}
    </div>
  </div>
);
export async function getServerSideProps(context) {
  // const user_id = 1;
  // try {
  //   const res = await axios.get(`http://localhost:8004/feed/${user_id}`);
  //   const feed = res.data.data;
  //   return {
  //     props: {
  //       feed,
  //     },
  //   };
  // } catch (err) {
  //   return {
  //     props: {
  //       feed: [],
  //     },
  //   };
  // }
  const feed = mockFeedData;
  return {
    props: {
      feed,
    },
  };
}

export default Timeline;
