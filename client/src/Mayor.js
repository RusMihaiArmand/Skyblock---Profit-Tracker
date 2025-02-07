import {useState} from 'react'


const Mayor = () => {

  const [mayor, setMayor ] = useState('???');

  const fetchMayor = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/mayor");
      const data = await response.json();

      console.log(data);

      if (data.message === "ERROR") setMayor("ERROR FETCHING NAME1");
      else setMayor(data.mayor);
    } catch (error) {
      setMayor("ERROR FETCHING NAME2");
      console.error("Error fetching message:", error);
    }
  };


   return (
    <div className="Mayors">
      <h1>MAYORS GO HERE</h1>

      <br></br>

      <p> {mayor} </p>

      <br></br>
      
     <button className="buttonS1" onClick={fetchMayor}> LOG IN </button>
      
    </div>
  );
}

export default Mayor;