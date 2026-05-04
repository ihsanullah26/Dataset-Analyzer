export default function ClassifierModelSelector({text})
{
    return (
            <div>
            <h1 className="text-red-500 font-bold mt-2">Select One Model For Training</h1>
            <select defaultValue="" 
                onChange={(e) => text(e.target.value)} className="border border-green-800 rounded-xl">
                <option value="" disabled>Choose a Model</option>
                <option value="Linear">Linear Classifier</option>
                <option value="DecisionTree">Decision Tree Classifier</option>
                <option value="RandomForest">Random Forest Classifier</option>
            </select>
        </div>
    );
}