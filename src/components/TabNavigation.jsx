import { TrendingUp, BarChart4 } from 'lucide-react';

export default function TabNavigation({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'market', label: 'Market', icon: TrendingUp },
    { id: 'analytics', label: 'Analytics', icon: BarChart4 }
  ];

  return (
    <div className="bg-slate-900 border-b border-slate-700">
      <div className="flex">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                flex items-center gap-2 px-6 py-4 border-b-2 transition-all
                ${
                  isActive
                    ? 'border-green-500 text-green-400 bg-slate-800'
                    : 'border-transparent text-slate-400 hover:text-slate-300 hover:bg-slate-800/50'
                }
              `}
            >
              <Icon size={20} />
              <span className="font-medium">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
