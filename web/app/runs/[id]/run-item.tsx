import { format } from "date-fns";

const RunItem = ({ run }: { run: any }) => (
  <div className="border-2 border-black rounded-sm p-6 mb-4 shadow">
    <h2 className="font-bold text-2xl mb-2">{run.id}</h2>
    <p className="font-semibold">Status: {run.status}</p>
    <p className="font-semibold">Job type: {run.job_type}</p>
    <p className="text-sm text-gray-500 mb-2">
      Created At: {format(new Date(run.created_at), "MM/dd/yyyy")}
    </p>
  </div>
);

export default RunItem;
