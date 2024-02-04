import { cache } from "react";
import "server-only";

const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT;

const fetchData = async (url: string) => {
  try {
    const res = await fetch(`${API_ENDPOINT}/${url}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch data");
    return res.json();
  } catch (error) {
    console.error(`Error fetching data: ${error.message}`);
    throw error;
  }
};

export const getFeedItems = async (user_id: string) =>
  fetchData(`feed/${user_id}`);
export const getSubscriptions = async (user_id: number) =>
  fetchData(`subscriptions/?user_id=${user_id}`);
export const getPendingRuns = async () => fetchData("runs");
export const getUser = async (user_id: number) => fetchData(`user/${user_id}`);
