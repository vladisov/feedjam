import React from "react";
import RunItem from "./run-item";

interface RunsProps {
  params: { slug: string };
}

const Runs: React.FC<RunsProps> = ({ params }) => {
  // const runs = params.runs;
  const runs: any[] = [];

  return (
    <div className="max-w-2xl mx-auto px-4">
      <h1 className="text-3xl font-bold mb-6">Your Runs</h1>
      {runs.map((run) => (
        <RunItem key={run.id} run={run} />
      ))}
    </div>
  );
};

export default Runs;
