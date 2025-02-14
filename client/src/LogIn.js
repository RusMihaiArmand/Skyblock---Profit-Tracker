import {testClick} from "./functions";
import {useState} from 'react'


const LogIn = () => {

  const [userName, setUserName] = useState('');
  const [profile, setProfile] = useState('');
  const [key, setKey] = useState('');


  const filterLogInData = async () => {

    console.log('USER = ' , userName);
    console.log('PROFILE = ' , profile);
    

    const url = new URL("http://127.0.0.1:5000/player");

    if (userName) url.searchParams.append("name", userName); 
    if (profile) url.searchParams.append("profile", profile); 
    if (key) url.searchParams.append("key", key);  



    try {
      const response = await fetch(url);
      const data = await response.json();

      console.log(data.message);
    } catch (error) {
      console.error("Error fetching player data: ", error);
    }
    

  };




  return (
    <div className="??">
      <h1>LOGIN GO HERE</h1>

      <div>
        <label>Username:</label>
        <input type="text"  id="userName"  value={userName}  onChange={(e) => setUserName(e.target.value)} />
      </div>

      <br></br>
      <br></br>

      <div>
        <label>Profile:</label>
        <input type="text"  id="profile"  value={profile}  onChange={(e) => setProfile(e.target.value)} />
      </div>


      <br></br>
      <br></br>

      <div>
        <label>Key:</label>
        <input type="text"  id="key"  value={key}  onChange={(e) => setKey(e.target.value)} />
      </div>


      <br></br>
      <br></br>

      <button className="buttonS1" onClick={filterLogInData}> LOG IN </button>

    </div>
  );
}

export default LogIn;