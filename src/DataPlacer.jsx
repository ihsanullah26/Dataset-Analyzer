import { useState } from "react";
import { DocumentPlusIcon } from "@heroicons/react/24/outline";
import ModelSelector from './ModelSelector.jsx';

export default function DataPlacer() {
  const [selectedfile, SetFileName] = useState(null);
  const HandlefileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      SetFileName(file);
    }
  };

  const isSelected = selectedfile ? "text-green-600 font-bold" : "text-red-400 font-bold";

  return (
    /* Added 'flex' class and ensured 'flex-col' works */
    <div className="flex flex-col gap-3 justify-center items-center  bg-white shadow-lg rounded-3xl border-white/50 h-max w-102 p-8">
      {/* Changed <title> to <h2> */}

      <h2 className="text-2xl font-bold text-pink-600">Data Placer</h2>
      <label
        htmlFor="dataset"
        className={`${selectedfile && "border border-green-500 rounded-xl"}`}
      >
        <DocumentPlusIcon className="size-12 transition-all duration-300 ease-in-out
        hover:bg-pink-200 hover:shadow-2xl hover:-translate-y-2 hover:border-green-300 hover:rounded-xl" />
      </label>
      <input
        type="file"
        name="dataset"
        id="dataset"
        accept=".csv"
        onChange={HandlefileChange}
        className={`hidden p-12 ${selectedfile ? "border border-green-500 rounded-xl" : "border border-red-500"} `}
      />
      <div className="bg-pink-200 w-full p-1 rounded-lg">
        <p
          className={`${isSelected}`}
        >
          Selected file: {selectedfile ? selectedfile.name : "No file selected"}
        </p>
        <p
          className={`${isSelected}`}
        >
          Size :{" "}
          {selectedfile
            ? `${(selectedfile.size / 1024).toFixed(2)} KB`
            : "0 bytes"}
        </p>
      </div>
      {selectedfile && <ModelSelector csvFile={selectedfile} />}
    </div>
  );
}