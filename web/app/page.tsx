import React from "react";
import FeedItem from "./components/feed-item";
import Link from "next/link";
import { mockFeedData } from "./feed";
import "../styles/main.css";
import { getFeedItems } from "./utils";

interface TimelineProps {}

const Timeline: React.FC<TimelineProps> = async () => {
  const feed = (await getFeedItems("1")).user_feed_items;
  console.log(feed);

  return (
    <div className="flex flex-col items-center justify-center px-4 font-nunito my-10">
      <nav className="flex flex-row items-center justify-center mb-6 w-1/2 text-2xl font-semibold">
        <Link href="/subscriptions" className=" border-r border-black pr-2">
          Subscriptions
        </Link>
        <Link href="/runs" className=" border-r  border-black px-2">
          Runs
        </Link>
        <Link href="/account" className=" border-black pl-2">
          Account
        </Link>
      </nav>
      <div className="items-start w-1/2 max-w-4xl">
        {feed.map((item: { feed_item_id: React.Key }) => (
          <FeedItem key={item.feed_item_id} item={item} />
        ))}
      </div>
    </div>
  );
};

export default Timeline;
