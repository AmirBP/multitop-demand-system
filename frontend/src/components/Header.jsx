import { Link, useLocation } from "react-router-dom";

const NavLink = ({ to, children }) => {
  const { pathname } = useLocation();
  const active = pathname === to;
  return (
    <Link
      to={to}
      className={`px-3 py-1 rounded-lg ${active ? "bg-white text-slate-900" : "hover:underline"}`}
    >
      {children}
    </Link>
  );
};

const Header = () => {
  return (
    <header className="bg-slate-900 text-white px-6 py-3 flex justify-between items-center">
      <h1 className="text-lg font-bold">MultiTop Demand System</h1>
      <nav className="space-x-2 text-sm">
        <NavLink to="/">📈 Predicción</NavLink>
        <NavLink to="/entrenamiento">🧠 Entrenamiento</NavLink>
        <NavLink to="/dashboard">📊 Dashboard</NavLink>
      </nav>
    </header>
  );
};
export default Header;