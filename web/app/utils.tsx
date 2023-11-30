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

export const getSubscriptions = async (user_id: string) => {
  const res = await fetch(`${API_ENDPOINT}/subscriptions/${user_id}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch data");
  }

  return res.json();
};

export const getPendingRuns = async () => {
  const res = await fetch(`${API_ENDPOINT}/runs`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch data");
  }

  return res.json();
};

export const getUser = async (user_id: number) => {
  const res = await fetch(`${API_ENDPOINT}/user/${user_id}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch data");
  }

  return res.json();
};
