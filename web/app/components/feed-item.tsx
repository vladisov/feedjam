import { format } from "date-fns";
import { IconFeedback } from "./icon-feedback";

const FeedItem = ({ item }: { item: any }) => {
  return (
    <div className="flex flex-col  p-6 mb-6 border border-black rounded-md overflow-hidden">
      <div className="flex flex-row justify-between">
        <h3 className="text-2xl mb-2 font-bold items-center">{item.title}</h3>
        <div className="flex flex-row items-start">
          <span className="text-2xl leading-6 font-light mx-2 items-center justify-center">
            [{item.points}]
          </span>
          <IconFeedback direction="up" />
          <IconFeedback direction="down" />
        </div>
      </div>

      <div className="flex flex-col font-light">
        <div>
          <p className="mb-4 text-base leading-relaxed line-clamp-3 overflow-hidden">
            {item.summary}
          </p>
        </div>
      </div>
      <div className="flex justify-between">
        <div className="flex flex-row ">
          <a
            href={item.article_url}
            className="hover:text-yellow-700 mb-2 block mr-2 border-r border-black pr-2"
          >
            Source
          </a>
          <a href={item.comments_url} className=" hover:text-yellow-700">
            Comments
          </a>
        </div>
        <div> {item.source_name}</div>
      </div>
    </div>
  );
};

export default FeedItem;
