import { format } from "date-fns";

const FeedItem = ({ item }: { item: any }) => (
  <div className="flex flex-col p-6 mb-6 border-2 border-black rounded-sm overflow-hidden">
    <div className="flex flex-row justify-between">
      <h3 className="text-2xl mb-2 font-bold items-center">{item.title}</h3>
      <div className="flex flex-row items-start">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-6 h-6"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"
          />
        </svg>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-6 h-6 ml-2"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3"
          />
        </svg>
      </div>
    </div>

    <div className="flex flex-col font-light">
      <div>
        <p className="mb-4 text-base leading-relaxed line-clamp-3 overflow-hidden">
          {item.description}
        </p>
      </div>
      <p className="mb-2">Points: {item.points}</p>
      <a href={item.article_url} className=" hover:text-sky-700 mb-2 block">
        Go to source
      </a>
      <a href={item.comments_url} className=" hover:text-sky-700">
        Comments
      </a>
    </div>
  </div>
);

export default FeedItem;
