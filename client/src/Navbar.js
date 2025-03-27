import { Link } from 'react-router-dom'

const Navbar = () => {
    return (
        <nav className="Navbar">

            <h1>MENU</h1>

            <div>

                <Link to="/">Home</Link>
                <br></br>
                <Link to="/mayor">Mayor</Link>
                <br></br>
                <Link to="/login">Login</Link>
                <br></br>
                <Link to="/craft">Craft</Link>

            </div>
    

        </nav>
    );
}

export default Navbar;