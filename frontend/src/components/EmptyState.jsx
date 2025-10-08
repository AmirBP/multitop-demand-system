const EmptyState = ({ title, subtitle, action }) => (
  <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center text-slate-600">
    <p className="text-lg font-semibold mb-1">{title}</p>
    <p className="text-sm mb-3">{subtitle}</p>
    {action}
  </div>
);
export default EmptyState;