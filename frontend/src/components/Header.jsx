import { Link } from "react-router-dom";

const Header = () => {
  return (
    <header className="bg-gray-800 text-white p-4 flex justify-between">
      <h1 className="text-lg font-bold">MultiTop Demand System</h1>
      <nav className="space-x-4">
        <Link to="/" className="hover:underline">📈 Predicción</Link>
        <Link to="/entrenamiento" className="hover:underline">🧠 Entrenamiento</Link>
        {/* <Link to="/dashboard" className="hover:underline">📊 Dashboard</Link> */}
      </nav>
    </header>
  );
};

export default Header;