import {testClick} from "./functions";


const LogIn = () => {
  return (
    <div className="??">
      <h1>LOGIN GO HERE</h1>

      <div>
        <label>Username:</label>
        <input type="text" id="usernameInput" name="usernameInput"></input>
      </div>

      <br></br>
      <br></br>

      <div>
        <label>Profile:</label>
        <input type="text" id="profileInput" name="profileInput"></input>
      </div>


      <br></br>
      <br></br>

      <button className="buttonS1" onClick={testClick}> LOG IN </button>

    </div>
  );
}

export default LogIn;