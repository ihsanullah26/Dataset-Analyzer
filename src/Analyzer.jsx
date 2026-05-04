import { useState, useEffect } from 'react';
import OriginalDataSection from './OriginalDataSection';
import HealedDataSection from './HealedDataSection';

export default function AnalysisComparison({ csvFile, originalMetrics, modelType, modelName, onBack }) {
    const [healedMetrics, setHealedMetrics] = useState(null);
    const [qualityScore, setQualityScore] = useState(null);
    const [healedDataset, setHealedDataset] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const handleDownload = () => {
        if (!healedDataset) return alert("Dataset not ready.");
        const url = window.URL.createObjectURL(healedDataset);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `healed_${modelName}.csv`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        window.URL.revokeObjectURL(url);
    };

    useEffect(() => {
        const performAnalysisAndRetrain = async () => {
            setLoading(true);
            try {
                const repairData = new FormData();
                repairData.append("file", csvFile);
                repairData.append("modelType", modelType);

                const repairRes = await fetch("http://127.0.0.1:8000/analyze_and_fill_gap", {
                    method: "POST",
                    body: repairData,
                });

                if (!repairRes.ok) throw new Error("Data repair failed.");

                const score = repairRes.headers.get("X-Quality-Score");
                setQualityScore(score && score !== "N/A" ? parseFloat(score).toFixed(4) : "N/A");
                
                const blob = await repairRes.blob();
                setHealedDataset(blob);

                const trainData = new FormData();
                trainData.append("file", blob, "healed_data.csv");
                trainData.append("modelType", modelType);
                trainData.append("modelName", modelName);

                const trainRes = await fetch("http://127.0.0.1:8000/train", {
                    method: "POST",
                    body: trainData,
                });

                const trainResult = await trainRes.json();
                setHealedMetrics(trainResult.metrics);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        performAnalysisAndRetrain();
    }, [csvFile, modelType, modelName]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-20 bg-white rounded-3xl shadow-xl border border-gray-100">
                <div className="w-12 h-12 border-4 border-pink-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-gray-500 font-bold animate-pulse">Processing Synthetic Logic...</p>
            </div>
        );
    }

    return (
        <div className="w-full max-w-2xl mx-auto bg-slate-50 rounded-[2rem] shadow-2xl border border-white overflow-hidden">
            <div className="p-6 bg-white border-b border-gray-100 flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-black text-gray-800">Analysis Results</h2>
                    <p className="text-xs font-bold text-pink-500 uppercase tracking-tighter">{modelName} {modelType}</p>
                </div>
                <button onClick={onBack} className="bg-gray-900 text-white text-xs px-5 py-2.5 rounded-full font-bold hover:scale-105 transition-transform">
                    ← Back
                </button>
            </div>

            <div className="max-h-[600px] overflow-y-auto p-6 space-y-8 custom-scrollbar">
                <OriginalDataSection 
                    modelType={modelType} 
                    originalMetrics={originalMetrics} 
                />
                
                <hr className="border-dashed border-gray-200" />

                <HealedDataSection 
                    modelType={modelType}
                    healedMetrics={healedMetrics}
                    qualityScore={qualityScore}
                    onDownload={handleDownload}
                    Dataset = {csvFile}
                />
            </div>
            <div className="h-6 bg-gradient-to-t from-slate-50 to-transparent"></div>
        </div>
    );
}