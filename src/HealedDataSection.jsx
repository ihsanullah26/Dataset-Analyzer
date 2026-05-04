import React, { useState } from 'react';
import GenerateSyntheticData  from './GenerateSyntheticData';

const StatCard = ({ label, value, color }) => (
    <div className="bg-white border border-gray-100 p-4 rounded-2xl shadow-sm flex-1 min-w-[140px] overflow-hidden">
        <p className="text-[10px] uppercase font-black text-gray-400 mb-1 tracking-widest">{label}</p>
        <p className={`text-xl font-bold truncate ${color}`}>{value ?? 'N/A'}</p>
    </div>
);

export default function HealedDataSection({ modelType, healedMetrics, qualityScore, onDownload, Dataset }) {
    const [generateData, setGenerateData] = useState(false);

    // If user clicked "Generate Data", swap the view
    if (generateData) {
        // Changed csvFile to Dataset since that is what you are passing as a prop
        return <GenerateSyntheticData csvFile={Dataset} onBack={() => setGenerateData(false)} />;
    }
    
    return (
        <section className="relative">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest">Healed Data Performance</h3>
                </div>
                <span className="bg-green-100 text-green-700 text-[9px] px-2 py-1 rounded font-black uppercase">Optimized</span>
            </div>

            {/* Synthetic Quality Banner */}
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-5 mb-4 text-white shadow-lg shadow-blue-100">
                <p className="text-[9px] font-black uppercase opacity-70 tracking-widest">Synthetic Quality Score</p>
                <p className="text-3xl font-black">{qualityScore}</p>
            </div>
            
            <div className="flex gap-4 mb-4">
                <StatCard 
                    label="Improved Metric" 
                    value={modelType === "Classification" ? healedMetrics?.accuracy.toFixed(2) : healedMetrics?.r2.toFixed(2)} 
                    color="text-green-600" 
                />
                <StatCard 
                    label="Task Type" 
                    value={modelType} 
                    color="text-gray-700" 
                />
            </div>

            <div className="bg-pink-200 rounded-2xl p-4 shadow-inner border border-green-900/30">
                <p className="text-[9px] text-gray-500 font-bold uppercase mb-2">Optimized Metrics Log</p>
                <pre className="text-[10px] text-red-700 font-bold font-mono leading-relaxed overflow-x-auto">
                    {healedMetrics?.classification_report || "Processing output..."}
                </pre>
            </div>

            <div className='flex gap-4 mt-6'>
                <button 
                    className='bg-pink-600 font-bold text-white border h-12 rounded-xl px-4 hover:bg-pink-500 hover:cursor-pointer transition-all' 
                    onClick={onDownload}
                >
                    Download Dataset
                </button>
                <button 
                    className='bg-pink-600 font-bold px-4 text-white border h-12 rounded-xl hover:bg-pink-500 hover:cursor-pointer transition-all'
                    onClick={() => setGenerateData(true)} 
                >
                    Generate Data
                </button>
            </div>
        </section>
    );
}