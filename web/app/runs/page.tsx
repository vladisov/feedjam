import axios from "axios";
import RunItem from "./[id]/run-item";

const Runs = () => {
  const runs: any[] = [];
  return (
    <div className="max-w-2xl mx-auto px-4 my-10 font-nunito">
      <h1 className="text-3xl font-bold mb-6">Your Runs</h1>
      {runs.map((run) => (
        <RunItem key={run.id} run={run} />
      ))}
    </div>
  );
};

export default Runs;
