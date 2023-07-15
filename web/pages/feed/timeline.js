import axios from "axios";
import Link from "next/link";

// This is a single feed item component
const FeedItem = ({ item }) => (
  <div>
    <h2>{item.title}</h2>
    <p>{item.description}</p>
    <Link href={item.article_url}>Read More</Link>
  </div>
);

// This is the main page component
const Timeline = ({ feed }) => (
  <div>
    <h1>Your Feed</h1>
    {feed.map((item) => (
      <FeedItem key={item.id} item={item} />
    ))}
  </div>
);

// This function runs on the server and fetches the data
export async function getServerSideProps(context) {
  const { user_id } = 1;

  // Call your API
  const res = await axios.get(`http://localhost:8004/feed/${user_id}`);
  const feed = res.data.data;

  return {
    props: {
      feed,
    },
  };
}

export default Timeline;
