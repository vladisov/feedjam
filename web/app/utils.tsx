import { cache } from "react";
import "server-only";

const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT;

export const getFeedItems = async (user_id: string) => {
  const res = await fetch(`${API_ENDPOINT}/feed/${user_id}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch data");
  }

  return res.json();
};
