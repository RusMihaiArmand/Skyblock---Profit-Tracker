import {testClick} from "./functions";
import {useState} from 'react'


const Craft = () => {



  const getCraftProfits = async () => {

    console.log('clicked');

    

    const url = new URL("http://127.0.0.1:5000/craft");

 

    try {
      const response = await fetch(url);
      const data = await response.json();

      console.log(data.message);
    } catch (error) {
      console.error("Error fetching craftables data: ", error);
    }
    

  };



  const updatePrices = async () => {

    console.log('clicked');

    

    const url = new URL("http://127.0.0.1:5000/prices");

 

    try {
      const response = await fetch(url);
      const data = await response.json();

      console.log(":)");
      console.log(data.message);
    } catch (error) {
      console.error("Error fetching prices data: ", error);
    }
    

  };




  return (
    <div className="??">
      <h1>CRAFTING PROFITS GO HERE</h1>

      <br></br><br></br><br></br>

      

      <button className="buttonS1" onClick={getCraftProfits}> DO IT </button><br></br><br></br>

      <button className="buttonS1" onClick={updatePrices}> DO IT - p </button>

    </div>
  );
}

export default Craft;