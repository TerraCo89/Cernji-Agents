/**
 * HelloCard - Simple test component for LangGraph Generative UI
 */

interface HelloCardProps {
  greeting: string;
  timestamp: string;
  testData: string;
}

export default function HelloCard({ greeting, timestamp, testData }: HelloCardProps) {
  const date = new Date(timestamp);

  return (
    <div className="rounded-xl border-2 border-blue-500 bg-blue-50 p-6 shadow-md max-w-md my-4">
      <h3 className="text-xl font-bold text-blue-900 mb-2">
        {greeting}
      </h3>

      <p className="text-gray-700 text-sm mb-3">
        {testData}
      </p>

      <p className="text-gray-500 text-xs italic">
        Generated at: {date.toLocaleString()}
      </p>
    </div>
  );
}
