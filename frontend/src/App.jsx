import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import PrediccionProductos from "./pages/PrediccionProductos";
import EntrenamientoModelo from "./pages/EntrenamientoModelo";
import DashboardGeneral from "./pages/DashboardGeneral";
import Header from "./components/Header";
import DemoCompleto from "./pages/DemoCompleto";
function App() {
  return (
    <Router>
      <Header />
      <Routes>
        <Route path="/" element={<PrediccionProductos />} />
        <Route path="/entrenamiento" element={<EntrenamientoModelo />} />
        <Route path="/dashboard" element={<DashboardGeneral />} />
        <Route path="/demo" element={<DemoCompleto />} /> 
      </Routes>
    </Router>
  );
}
export default App;
