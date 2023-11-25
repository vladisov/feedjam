import React from "react";
import FeedItem from "./feed-item";
import Link from "next/link";
import { mockFeedData } from "./feed";

interface TimelineProps {}

async function getData() {
  const res = await fetch("http://localhost:8004/feed/1");

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error("Failed to fetch data");
  }

  return res.json();
}

const Timeline: React.FC<TimelineProps> = async () => {
  // const feed_data = await fetch(
  //   "http://localhost:8004/runs?subscription_id=${subscription_id}"
  // );
  // const feed = mockFeedData;
  const feed = (await getData()).user_feed_items;
  console.log(feed);

  return (
    <div className="flex flex-col items-center justify-center  px-4 font-nunito mt-10">
      {/* <nav className="p-6 mb-6 border rounded-md shadow-md">
        <Link href="/subscriptions" className="text-sky-500 hover:text-sky-700">
          Subscriptions
        </Link>
        <Link href="/runs" className="ml-6 text-sky-500 hover:text-sky-700">
          Runs
        </Link>
      </nav> */}
      <div className="items-start  max-w-4xl">
        {feed.map((item) => (
          <FeedItem key={item.feed_item_id} item={item} />
        ))}
      </div>
    </div>
  );
};

export default Timeline;
