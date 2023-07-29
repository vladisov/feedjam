import faker from "faker";

function randomString(wordCount: number): string {
  return faker.lorem.words(wordCount);
}

export const mockFeedData = Array.from({ length: 10 }).map((_, i) => ({
  id: i,
  link: `https://www.example.com/link-${i}`,
  updated_at: new Date().toISOString(),
  local_id: `https://news.ycombinator.com/item?id=${i}`,
  comments_url: `https://news.ycombinator.com/item?id=${i}`,
  num_comments: Math.floor(Math.random() * 1000),
  title: randomString(3),
  source_id: 1,
  created_at: new Date().toISOString(),
  published: new Date().toISOString(),
  description: `<p>Article URL: <a href="https://www.example.com/link-${i}">https://www.example.com/link-${i}</a></p>
    <p>Comments URL: <a href="https://news.ycombinator.com/item?id=${i}">https://news.ycombinator.com/item?id=${i}</a></p>
    <p>Points: ${Math.floor(Math.random() * 100)}</p>
    <p># Comments: ${Math.floor(Math.random() * 1000)}</p>`,
  article_url: `https://www.example.com/link-${i}`,
  points: Math.floor(Math.random() * 100),
  summary: randomString(50), // 50 words summary
}));
