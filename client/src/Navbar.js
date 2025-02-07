import { Link } from 'react-router-dom'

const Navbar = () => {
    return (
        <nav className="Navbar">

            <h1>MENU</h1>

            <div>

                <Link to="/">Home</Link>
                <Link to="/mayor">Mayor</Link>

            </div>
            {/* <a href="/">Home</a>
            <a href="/login">LOGIN</a>
            <a href="/mayor">Mayor</a> */}


        </nav>
    );
}

export default Navbar;