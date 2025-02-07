import React, { useState, useEffect } from 'react';
import axios from 'axios';

import Navbar from "./Navbar";
import Home from "./Home";
import Mayor from "./Mayor";

import './index.css'


import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import LogIn from './LogIn';

function App() {
  const [message, setMessage] = useState('');
  const [mayorName, setMayorName] = useState("");

  const fetchMessage = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/hello");
      const data = await response.json();
      setMessage(data.message);
    } catch (error) {
      console.error("Error fetching message:", error);
    }
  };

  const fetchMayor = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/mayor");
      const data = await response.json();

      console.log(data);

      if (data.message === "ERROR") setMayorName("ERROR FETCHING NAME1");
      else setMayorName(data.mayor);
    } catch (error) {
      setMayorName("ERROR FETCHING NAME2");
      console.error("Error fetching message:", error);
    }
  };




  useEffect(() => {
    // Fetch data from the Python backend
    axios.get('http://localhost:5000/api/greet')
      .then(response => {
        setMessage(response.data.message);
      })
      .catch(error => {
        console.error("There was an error fetching the message!", error);
      });
  }, []);

 

  return (
    <Router>
      <div className="mainApp">
        <div className="navbar"><Navbar /></div>

        <div className="rest">
          <Routes>
            <Route exact path="/" element={<Home />} />
            <Route exact path="/mayor" element={<Mayor />} />
            <Route exact path="/login" element={<LogIn />} />

          </Routes>
        </div>
      </div>
    </Router>
  );




}

export default App;
