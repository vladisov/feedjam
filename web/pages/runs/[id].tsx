import axios from "axios";
import RunItem from "../../components/run-item";

const Runs = ({ runs }) => (
  <div className="max-w-2xl mx-auto px-4">
    <h1 className="text-3xl font-bold mb-6">Your Runs</h1>
    {runs.map((run) => (
      <RunItem key={run.id} run={run} />
    ))}
  </div>
);

Runs.getInitialProps = async (context) => {
  console.log(context.query.id);

  let subscription_id = context.query.subscription_id;

  const res = await axios.get(
    `http://localhost:8004/runs?subscription_id=${subscription_id}`
  );
  const runs = res.data;

  return {
    runs,
  };
};

export default Runs;
