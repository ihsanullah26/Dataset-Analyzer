import { useState } from "react"

export default function GenerateSyntheticData({ csvFile }) {
    const [SynthesizerType, setSynthesizerType] = useState("")
    const [rowCount, setRowCount] = useState(0)

    const [isLoading, setIsLoading] = useState(false)
    const [qualityScore, setQualityScore] = useState(null)
    const [csvContent, setCsvContent] = useState(null)

    const HandleGenerateData = async () => {
        if (!SynthesizerType) {
            alert("Select synthesizer")
            return
        }

        if (!rowCount || rowCount <= 0) {
            alert("Invalid row count")
            return
        }

        setIsLoading(true)

        const Data = new FormData()
        Data.append("file", csvFile)
        Data.append("Synthesizer", SynthesizerType)
        Data.append("Num_of_rows", rowCount)

        try {
            const response = await fetch("http://127.0.0.1:8000/GenerateRandomData", {
                method: "POST",
                body: Data
            })

            const result = await response.json()

            if (!response.ok) throw new Error(result.detail)

            // ✅ Score
            setQualityScore(result.quality_score)


            // ✅ Convert to CSV
            const headers = Object.keys(result.synthetic_data[0]).join(",")
            const rows = result.synthetic_data
                .map(obj => Object.values(obj).join(","))
                .join("\n")

            setCsvContent(`${headers}\n${rows}`)

        } catch (err) {
            console.error(err)
            alert("Error generating data")
        } finally {
            setIsLoading(false)
        }
    }

    const handleDownload = () => {
        if (!csvContent) return

        const blob = new Blob([csvContent], { type: "text/csv" })
        const url = window.URL.createObjectURL(blob)

        const a = document.createElement("a")
        a.href = url
        a.download = "synthetic_dataset.csv"
        a.click()

        window.URL.revokeObjectURL(url)
    }

    return (
        <div className="flex flex-col gap-3 p-4 ">
            <select
                value={SynthesizerType}
                onChange={(e) => setSynthesizerType(e.target.value)}
                className="bg-pink-200 h-8 rounded-xl px-2"
            >
                <option value="" disabled>Select Synthesizer</option>
                <option value="Guassian">Gaussian</option>
                <option value="CTGAN">CTGAN</option>
                <option value="TVAE">TVAE</option>
            </select>

            <input
                type="number"
                min={1}
                value={rowCount}
                onChange={(e) => setRowCount(Number(e.target.value))}
                className="bg-pink-200 h-8 rounded-xl text-center"
            />

            <button
                onClick={HandleGenerateData}
                disabled={isLoading}
                className="bg-black text-white rounded-xl h-8"
            >
                {isLoading ? "Generating..." : "Generate"}
            </button>

            {/* ✅ RESULTS */}
            {qualityScore !== null && (
                <h2 className="text-green-600 text-center font-bold">
                    Quality Score: {(qualityScore * 100).toFixed(2)}%
                </h2>
            )}

            {csvContent && (
                <button
                    onClick={handleDownload}
                    className="bg-blue-600 text-white rounded-xl h-10"
                >
                    Download CSV
                </button>
            )}
        </div>
    )
}