import {useState} from 'react'
import LogoImage from '../assets/hero.png'
export default function DataPlacer(){
    const [selectedfile, SetFileName] = useState(null)
    const HandlefileChange = (e) =>{
        const file = e.target.files[0]
        if(file) {
            SetFileName(file)
        }
    }

    return(
        /* Added 'flex' class and ensured 'flex-col' works */
        <div className="flex flex-col justify-center items-center  bg-white shadow-lg rounded-3xl border-white/50 h-max w-96 p-8">
            {/* Changed <title> to <h2> */}

            <h2 className="text-2xl font-bold text-pink-600">Data Placer</h2>
            <label htmlFor="dataset">
            <img src={LogoImage} alt="LogoImage" className={`w-32 ${selectedfile?'border border-green-500 rounded':'border border-red-500 rounded'}`}/>
            </label>
            <input 
                type="file" 
                name="dataset" 
                id="dataset" 
                accept=".csv"
                style={{display:'none'}}
                onChange={HandlefileChange} 
                className={`p-12 ${selectedfile?'border border-green-500 rounded-xl':'border border-red-500'} `}
            />
            <div className='bg-black w-full p-4 rounded-lg'>
            <p className={`mt-12 ${selectedfile?'text-green-600 font-bold':'text-red-400 font-bold'}`}>
                Selected file: {selectedfile ? selectedfile.name : 'No file selected'}   
            </p>
            <p className={`${selectedfile?'text-green-600 font-bold ':'text-red-400 font-bold'}`}>
                Size : {selectedfile ? `${(selectedfile.size / 1024).toFixed(2)} KB` : '0 bytes'}
            </p>
            </div>
        </div>
    )
}