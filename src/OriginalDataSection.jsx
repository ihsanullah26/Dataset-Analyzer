import React from 'react';

const StatCard = ({ label, value, color }) => (
    <div className="bg-white border border-gray-100 p-4 rounded-2xl shadow-sm flex-1 min-w-[140px] overflow-hidden">
        <p className="text-[10px] uppercase font-black text-gray-400 mb-1 tracking-widest">{label}</p>
        <p className={`text-xl font-bold truncate ${color}`}>{value ?? 'N/A'}</p>
    </div>
);

export default function OriginalDataSection({ modelType, originalMetrics }) {
    return (
        <section className="relative">
            <div className="flex items-center gap-2 mb-4">
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                <h3 className="text-sm font-black text-gray-500 uppercase tracking-widest">Original Data Baseline</h3>
            </div>
            
            <div className="flex gap-4 mb-4">
                <StatCard 
                    label="Accuracy / R2" 
                    value={modelType === "Classification" ? originalMetrics.accuracy.toFixed(2) : originalMetrics.r2.toFixed(2)} 
                    color="text-red-500" 
                />
                <StatCard 
                    label="Error Metric" 
                    value={modelType === "Classification" ? "N/A" : originalMetrics.mse.toFixed(2)} 
                    color="text-gray-700" 
                />
            </div>

            <div className="bg-pink-200 rounded-2xl p-4 shadow-inner">
                <p className="text-[9px] text-gray-600 font-bold uppercase mb-2">Metrics Log</p>
                <pre className="text-[10px] text-red-700 font-bold font-mono leading-relaxed overflow-x-auto">
                    {originalMetrics.classification_report || "No text report available"}
                </pre>
            </div>
        </section>
    );
}