const Loader = ({ text = "Cargando..." }) => (
  <div className="flex items-center gap-3 text-slate-700">
    <span className="h-3 w-3 rounded-full bg-slate-400 animate-pulse" />
    <span className="h-3 w-3 rounded-full bg-slate-400 animate-pulse delay-150" />
    <span className="h-3 w-3 rounded-full bg-slate-400 animate-pulse delay-300" />
    <span className="font-medium">{text}</span>
  </div>
);
export default Loader;
