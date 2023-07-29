import { format } from "date-fns";

const FeedItem = ({ item }) => (
  <div className="bg-white rounded-xl p-6 mb-6 shadow-md  border">
    <h3 className="text-2xl mb-2 font-bold">{item.title}</h3>
    <div className="font-light">
      <p className="mb-4 text-base leading-relaxed line-clamp-3 overflow-hidden">
        {item.summary}
      </p>
      <p className="mb-2">Points: {item.points}</p>
      <a
        href={item.article_url}
        className="text-sky-400 hover:text-sky-700 mb-2 block"
      >
        Go to source
      </a>
      <a href={item.comments_url} className="text-sky-400 hover:text-sky-700">
        Comments
      </a>
    </div>
  </div>
);

export default FeedItem;
