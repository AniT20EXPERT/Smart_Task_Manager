import { useState, useEffect } from 'react';
import { CheckCircle2, MessageSquare, BarChart3, Plus } from 'lucide-react';
import TaskInputSection from './components/TaskInputSection';
import ScheduleVisualizationSection from './components/ScheduleVisualizationSection';
import AIInteractionSection from './components/AIInteractionSection';
import Notification from './components/Notification';
import { Task, NotificationType } from './types';
import { useElectron } from './hooks/useElectron';

function App() {
  const [activeSection, setActiveSection] = useState<'task-input' | 'schedule-viz' | 'ai-interaction'>('task-input');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [notification, setNotification] = useState<{
    message: string;
    type: NotificationType;
    show: boolean;
  }>({ message: '', type: 'success', show: false });
  
  const [manualSchedule, setManualSchedule] = useState<any[]>([]);
  const [aiSchedule, setAiSchedule] = useState<any[]>([]);
  const [manualAlgo, setManualAlgo] = useState<string>('RR');
  const [quantum, setQuantum] = useState<string>('2');
  const [aiAlgo, setAiAlgo] = useState<string>('Not suggested yet');
  const [aiQuantum, setAiQuantum] = useState<string>('Not suggested yet');
  const [agentAlgo, setAgentAlgo] = useState<string>('Not suggested yet');
  const [agentQuantum, setAgentQuantum] = useState<string>('Not suggested yet');
  const [agentSchedule, setAgentSchedule] = useState<any[]>([]);
  const [resetMemorySchedule, setResetMemorySchedule] = useState<any[]>([]);

  // Electron integration
  const { isElectron, showNotification: showElectronNotification, setupMenuListeners } = useElectron();

  const showNotification = (message: string, type: NotificationType) => {
    setNotification({ message, type, show: true });
    
    // Also show native notification if in Electron
    if (isElectron) {
      showElectronNotification('Smart AI Task Scheduler', message);
    }
    
    setTimeout(() => {
      setNotification(prev => ({ ...prev, show: false }));
    }, 3000);
  };

  // Handle menu events from Electron
  useEffect(() => {
    if (isElectron) {
      setupMenuListeners(() => {
        setActiveSection('task-input');
        showNotification('Ready to add a new task!', 'info');
      });
    }
  }, [isElectron, setupMenuListeners]);

  const navItems = [
    {
      id: 'task-input',
      label: 'Task Input & Agentic AI Assistance',
      icon: <Plus className="w-5 h-5" />
    },
    {
      id: 'schedule-viz',
      label: 'Schedule Visualization Tab',
      icon: <BarChart3 className="w-5 h-5" />
    },
    {
      id: 'ai-interaction',
      label: 'AI Interaction Panel',
      icon: <MessageSquare className="w-5 h-5" />
    }
  ];

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'task-input':
        return <TaskInputSection 
        tasks={tasks} 
        setTasks={setTasks} 
        showNotification={showNotification} 
        setManualSchedule={setManualSchedule}
        setAiSchedule={setAiSchedule}
        manualAlgo={manualAlgo}
        setManualAlgo={setManualAlgo}
        quantum={quantum}
        setQuantum={setQuantum}
        aiAlgo={aiAlgo}
        setAiAlgo={setAiAlgo}
        aiQuantum={aiQuantum}
        setAiQuantum={setAiQuantum}
        navigate={setActiveSection}/>;
      case 'schedule-viz':
        return <ScheduleVisualizationSection 
        showNotification={showNotification} 
        manualSchedule={manualSchedule} 
        aiSchedule={aiSchedule} 
        manualAlgo={manualAlgo}
        quantum={quantum}
        aiAlgo={aiAlgo}
        aiQuantum={aiQuantum}
        navigate={setActiveSection}
        agentAlgo={agentAlgo}
        agentQuantum={agentQuantum}
        agentSchedule={agentSchedule}
        setAgentAlgo={setAgentAlgo}
        setAgentQuantum={setAgentQuantum}
        setAgentSchedule={setAgentSchedule}
        resetMemorySchedule={resetMemorySchedule}
        setResetMemorySchedule={setResetMemorySchedule}
        />;
      case 'ai-interaction':
        return <AIInteractionSection 
        tasks={tasks} 
        showNotification={showNotification} 
        agentAlgo={agentAlgo}
        agentQuantum={agentQuantum}
        agentSchedule={agentSchedule}
        resetMemorySchedule={resetMemorySchedule}
        setAgentSchedule={setAgentSchedule}
        />;
      default:
        return <TaskInputSection 
        tasks={tasks} 
        setTasks={setTasks} 
        showNotification={showNotification} 
        setManualSchedule={setManualSchedule}
        setAiSchedule={setAiSchedule}
        manualAlgo={manualAlgo}
        setManualAlgo={setManualAlgo}
        quantum={quantum}
        setQuantum={setQuantum}
        aiAlgo={aiAlgo}
        setAiAlgo={setAiAlgo}
        aiQuantum={aiQuantum}
        setAiQuantum={setAiQuantum}
        navigate={setActiveSection}
        />
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Title Bar */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            <h1 className="text-2xl font-bold text-white">Smart AI Task Scheduler</h1>
          </div>
          {isElectron && (
            <div className="flex items-center space-x-2 text-sm text-slate-400">
              <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              <span>Desktop App</span>
            </div>
          )}
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Sidebar Navigation */}
        <nav className="w-80 bg-slate-800 border-r border-slate-700 p-4">
          <div className="space-y-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id as any)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-all duration-200 ${
                  activeSection === item.id
                    ? 'bg-emerald-600 text-white shadow-lg transform scale-[1.02]'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                {item.icon}
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto">
          {renderActiveSection()}
        </main>
      </div>

      {/* Notification */}
      {notification.show && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(prev => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}

export default App;