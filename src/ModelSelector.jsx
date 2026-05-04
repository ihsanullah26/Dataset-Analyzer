import { useState } from 'react';
import SelectregressionModel from './RegressionModelSelector.jsx';
import SelectClassifierModel from './ClassifierModelSelector.jsx';
import ModelReport from './ModelReport.jsx';
import Analyzer from './Analyzer.jsx';

export default function ModelSelector({ csvFile }) {
    const [ModelType, SetModelType] = useState("");
    const [ModelName, SetModelName] = useState("");
    const [Modelinfo, SetModelReport] = useState("");
    const [error, setError] = useState("");
    const [showAnalysis, setShowAnalysis] = useState(false); // New state to toggle screens

    // Function to handle when the user clicks the train button
    const HandleTraining = async () => {
        setError("");
        SetModelReport("");

        if (!ModelType || !ModelName) {
            alert("Please select a model type and model name before training.");
            return;
        }

        const data = new FormData();
        data.append("file", csvFile);
        data.append("modelType", ModelType);
        data.append("modelName", ModelName);

        try {
            const response = await fetch("http://127.0.0.1:8000/train", { method: "POST", body: data });
            const result = await response.json();
            if (!response.ok) {
                setError("An unexpected error occurred during training.");
                return;
            }
            SetModelReport(result.metrics);
        } catch (err) {
            alert(err);
        }
    };

    // If the user clicked proceed, show the Analyzer component instead
    if (showAnalysis) {
        return (
            <Analyzer 
                csvFile={csvFile} 
                originalMetrics={Modelinfo} 
                modelType={ModelType} 
                modelName={ModelName} 
                onBack={() => setShowAnalysis(false)} 
            />
        );
    }

    return (
        <div className="bg-pink-200 p-2 w-full rounded shadow-xl">
            <h1 className="text-red-500 font-bold">Which Type of Models You want to be Your data Train on?</h1>
            
            <select 
                name="ModelType" 
                value={ModelType} 
                onChange={(e) => SetModelType(e.target.value)} 
                className="border border-green-800 rounded-xl"
            >
                <option value="" disabled>Select one Type</option>
                <option value="Regression">Regression</option>
                <option value="Classification">Classification</option>
            </select>

            {ModelType === "Regression" && <SelectregressionModel text={SetModelName} />}
            {ModelType === "Classification" && <SelectClassifierModel text={SetModelName} />}

            {error && (
                <div className="mt-3 p-2 bg-red-500 text-white font-bold rounded-lg text-sm">
                    {error}
                </div>
            )}

            <div className="flex gap-2">
                <button 
                    className="bg-black border border-white rounded-xl text-white mt-3 px-4 h-9 hover:bg-pink-400 hover:text-black" 
                    onClick={HandleTraining}
                >
                    Train
                </button>

                {/* Only show Proceed button if the original model has been trained successfully */}
                {Modelinfo && (
                    <button 
                        className="bg-blue-600 border border-white rounded-xl text-white mt-3 px-4 h-9 hover:bg-blue-400" 
                        onClick={() => setShowAnalysis(true)}
                    >
                        Proceed→
                    </button>
                )}
            </div>

            {!error && ModelName && ModelType && Modelinfo && (
                <div className="mt-4 p-3 bg-white rounded shadow-inner">
                    <h2 className="font-bold text-gray-700 mb-2">Original Data Results:</h2>
                    <ModelReport report={Modelinfo} />
                </div>
            )}
        </div>
    );
}