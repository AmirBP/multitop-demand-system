const StatCard = ({ title, value, icon, color = "bg-white" }) => (
  <div className={`${color} p-5 rounded-xl shadow flex items-center justify-between`}>
    <div>
      <p className="text-sm text-gray-600">{title}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
    <div className="bg-gray-100 p-3 rounded-full">{icon}</div>
  </div>
);
export default StatCard;
