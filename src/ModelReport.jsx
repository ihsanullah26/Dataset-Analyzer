// Destructure 'report' to match the prop name passed above
export default function ModelReport({ report }) {
  if (!report) return null;

  return (
    <div className="bg-pink-300 font-bold border rounded-xl mt-4 p-4 text-green-800">
      <h2 className="text-xl mb-2 underline">Model Performance</h2>
      
      {/* Display values conditionally based on what's available */}
      {report.mse !== null && <p>Mean Squared Error: {report.mse.toFixed(2)}</p>}
      {report.r2 !== null && <p>R2 Score: {report.r2.toFixed(2)}</p>}
      {report.accuracy !== null && <p>Accuracy: {report.accuracy.toFixed(2)}</p>}
      
      {report.classification_report && (
        <div className="mt-2">
          <p>Classification Report:</p>
          <pre className="font-mono text-[8px] bg-white bg-opacity-50 rounded p-3 overflow-x-auto whitespace-pre pr-2">
            {report.classification_report}
          </pre>
        </div>
      )}
      
    </div>
  );
}