import React from "react";
import { getUser } from "../utils";
import { format } from "date-fns";

interface AccountPageProps {}

const AccountPage: React.FC = async ({}: AccountPageProps) => {
  const user = await getUser(1);

  return (
    <div className="max-w-2xl mx-auto px-4 my-10 font-nunito">
      <h1 className="text-3xl font-bold mb-6">Account details</h1>

      <div className="border-2 border-black rounded-sm p-6 mb-4">
        <p className="font-semibold">User ID: {user.id}</p>
        <p className="font-semibold">Username: {user.name}</p>
        <p className="font-semibold">Is active: {user.is_active}</p>
        <p className="text-sm text-gray-500 mb-2">
          Created at: {format(new Date(user.created_at), "MM/dd/yyyy")}
        </p>
      </div>
    </div>
  );
};

export default AccountPage;
