import React, { useState } from 'react';
import { Play, Trash2, Download, Upload, AlertTriangle, Lightbulb, ClipboardCheck  } from 'lucide-react';
import { Task, NotificationType } from '../types';
import { apiCall } from '../utils/api';
import { API_URL } from '../utils/backend_config';

interface TaskInputSectionProps {
  tasks: Task[];
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  showNotification: (message: string, type: NotificationType) => void;
  setManualSchedule: React.Dispatch<React.SetStateAction<any[]>>;
  setAiSchedule: React.Dispatch<React.SetStateAction<any[]>>;
  manualAlgo: string;
  setManualAlgo: React.Dispatch<React.SetStateAction<string>>;
  quantum: string;
  setQuantum: React.Dispatch<React.SetStateAction<string>>;
  aiAlgo: string;
  setAiAlgo: React.Dispatch<React.SetStateAction<string>>;
  aiQuantum: string;
  setAiQuantum: React.Dispatch<React.SetStateAction<string>>;
  navigate: React.Dispatch<React.SetStateAction<'task-input' | 'schedule-viz' | 'ai-interaction'>>;
}


export default function TaskInputSection({
  tasks,
  setTasks,
  showNotification,
  setManualSchedule,
  setAiSchedule,
  manualAlgo,
  setManualAlgo,
  quantum,
  setQuantum,
  aiAlgo,
  setAiAlgo,
  aiQuantum,
  setAiQuantum,
  navigate,
}: TaskInputSectionProps){
  // Form state variables
  const [taskName, setTaskName] = useState('');
  const [duration, setDuration] = useState('');
  const [arrivalHrs, setArrivalHrs] = useState('');
  const [arrivalDate, setArrivalDate] = useState('');
  const [deadlineHrs, setDeadlineHrs] = useState('');
  const [deadlineDate, setDeadlineDate] = useState('');
  const [importance, setImportance] = useState<'High' | 'Medium' | 'Low'>('Medium');
  const [nlTask, setNlTask] = useState('');
  const [nlResponse, setNlResponse] = useState('');
  const [entryType, setEntryType] = useState<'nl' | 'form'>('form'); // default to form entry

  // Tab state
  const [activeTab, setActiveTab] = useState<'warning' | 'suggestions' | 'summary'>('warning');
  const [warningMsg, setWarningMsg] = useState('No warnings detected.');
  const [suggestionMsg, setSuggestionMsg] = useState('No suggestions available.');
  const [tasksSummaryMsg, setTasksSummaryMsg] = useState(['No tasks summary available.']);

  // Scheduler state
  // const [manualAlgo, setManualAlgo] = useState('RR');
  // const [quantum, setQuantum] = useState('2');
  // const [aiAlgo, setAiAlgo] = useState('Not suggested yet');
  // const [aiQuantum, setAiQuantum] = useState('Not suggested yet');
  const [deleteIds, setDeleteIds] = useState('');

  const handleValidateTask = async (nlTask: string, nlResponse: string, warningMsg: string, suggestionMsg: string, tasksSummaryMsg: any[]) => {
    const [success, data] = await apiCall(API_URL + '/api/validateTask','POST', { nlTask: nlTask, nlResponse: nlResponse, warningMsg: warningMsg, suggestionMsg: suggestionMsg, tasksSummaryMsg: tasksSummaryMsg });
    console.log(success, data);
    if (success) {
      setWarningMsg(data.warningMsg);
      setSuggestionMsg(data.suggestionMsg);
      setTasksSummaryMsg(data.tasksSummaryMsg);
      showNotification('Task validation processed successfully', 'success');
    } else {
      showNotification('Task validation failed', 'error');
    }
  };

  const handleAddTask = async (type: 'nl' | 'form') => {
  if (type === 'form') {
    // Original form entry logic
    if (!taskName || !duration || !arrivalHrs || !arrivalDate || !deadlineHrs || !deadlineDate) {
      showNotification('Please fill in all required fields', 'error');
      return;
    }

    // const success = await apiCall('/api/addTask');
    const success = true;
    if (success) {
      const newTask: Task = {
        id: Date.now(),
        taskName,
        duration: parseInt(duration),
        arrivalTime: {
          hrs: parseInt(arrivalHrs),
          date: arrivalDate,
        },
        deadlineTime: {
          hrs: parseInt(deadlineHrs),
          date: deadlineDate,
        },
        importance,
      };

      setTasks(prev => [...prev, newTask]);

      // Reset form
      setTaskName('');
      setDuration('');
      setArrivalHrs('');
      setArrivalDate('');
      setDeadlineHrs('');
      setDeadlineDate('');
      setImportance('Medium');
      setNlTask('');

      showNotification('Task added successfully', 'success');
    } else {
      showNotification('Failed to add task', 'error');
    }
  } else if (type === 'nl') {
    // NL entry logic: use tasksSummaryMsg array directly
    if (!tasksSummaryMsg || tasksSummaryMsg.length === 0) {
      showNotification('No natural language tasks available to add.', 'error');
      return;
    }

    const success = await apiCall('/api/addTask');
    if (success) {
      const newTasks: Task[] = tasksSummaryMsg.map((task: any, index: number) => ({
        id: Date.now() + index,
        taskName: task.TaskName || 'Untitled Task',
        duration: task.Duration ?? 1,
        arrivalTime: {
          hrs: task.arrivaltime ?? 0,
          date: task.arrivaldate ?? new Date().toISOString().split('T')[0],
        },
        deadlineTime: {
          hrs: task.deadlinetime ?? 0,
          date: task.deadlinedate ?? new Date().toISOString().split('T')[0],
        },
        importance: task.importance ?? 'Medium',
      }));

      setTasks(prev => [...prev, ...newTasks]);

      // Optionally reset tasksSummaryMsg
      setTasksSummaryMsg([]);

      showNotification('Natural language tasks added successfully!', 'success');
    } else {
      showNotification('Failed to add tasks from natural language input.', 'error');
    }
  }
};

  

  const handleDeleteAllTasks = async () => {
    const success = await apiCall('/api/deleteAllTasks');
    if (success) {
      setTasks([]);
      showNotification('All tasks deleted successfully', 'success');
    } else {
      showNotification('Failed to delete all tasks', 'error');
    }
  };

  const handleDeleteSpecificTasks = async () => {
    if (!deleteIds.trim()) {
      showNotification('Please enter task IDs to delete', 'error');
      return;
    }

    const success = await apiCall('/api/deleteTasks');
    if (success) {
      const idsToDelete = deleteIds.split(',').map(id => parseInt(id.trim()));
      setTasks(prev => prev.filter(task => !idsToDelete.includes(task.id)));
      setDeleteIds('');
      showNotification('Selected tasks deleted successfully', 'success');
    } else {
      showNotification('Failed to delete selected tasks', 'error');
    }
  };

  const handleExportTasks = async () => {
    const success = await apiCall('/api/exportTasks');
    if (success) {
      const dataStr = JSON.stringify(tasks, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      const exportFileDefaultName = 'tasks.json';
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      
      showNotification('Tasks exported successfully', 'success');
    } else {
      showNotification('Failed to export tasks', 'error');
    }
  };

  const handleImportTasks = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const importedTasks: Task[] = JSON.parse(text);
      
      const success = await apiCall('/api/importTasks');
      if (success) {
        setTasks(importedTasks);
        showNotification('Tasks imported successfully', 'success');
      } else {
        showNotification('Failed to import tasks', 'error');
      }
    } catch (error) {
      showNotification('Invalid JSON file format', 'error');
    }
    
    // Reset input
    event.target.value = '';
  };

  const handleRunManualScheduler = async (tasks: Task[], algo: string, quantum: string) => {
    const [success, data] = await apiCall(API_URL + '/api/run_scheduler', 'POST', { "task_list": tasks, "algo": algo, "tq": quantum });
    if (success) {
      setManualSchedule(data);
      setManualAlgo(algo);
      setQuantum(quantum);
      console.log(data);
      showNotification('Manual scheduler run successfully', 'success');

    } else {
      showNotification('Failed to run manual scheduler', 'error');
    }
  };

  const handleAISuggest = async (tasks: Task[]) => {
    console.log(JSON.stringify({ task_list: tasks }, null, 2));
    const [success, data] = await apiCall(API_URL + '/api/ai_suggest','POST', { "task_list": tasks });
    if (success) {
      setAiAlgo(data.algo);
      setAiQuantum(data.tq);
      showNotification('AI suggestion generated successfully', 'success');
    } else {
      showNotification('Failed to get AI suggestion', 'error');
    }
  };

  const handleRunAIScheduler = async (tasks: Task[], algo: string, quantum: string) => {
    const [success, data] = await apiCall(API_URL + '/api/run_scheduler', 'POST', { "task_list": tasks, "algo": algo, "tq": quantum });
    if (success) {
      setAiSchedule(data);
      setAiAlgo(algo);
      setAiQuantum(quantum);
      showNotification('AI scheduler run successfully', 'success');
    } else {
      showNotification('Failed to run AI scheduler', 'error');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-2 gap-6 h-full">
        {/* Left Panel - Form Entry */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-bold mb-6 text-emerald-400">Task Input & Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Task Name</label>
              <input
                type="text"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="Enter task name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Duration (hrs)</label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="Enter duration in hours"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Arrival Time (hrs)</label>
                <input
                  type="number"
                  value={arrivalHrs}
                  onChange={(e) => setArrivalHrs(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Hours"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Arrival Date</label>
                <input
                  type="date"
                  value={arrivalDate}
                  onChange={(e) => setArrivalDate(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Deadline Time (hrs)</label>
                <input
                  type="number"
                  value={deadlineHrs}
                  onChange={(e) => setDeadlineHrs(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Hours"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Deadline Date</label>
                <input
                  type="date"
                  value={deadlineDate}
                  onChange={(e) => setDeadlineDate(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Importance</label>
              <select
                value={importance}
                onChange={(e) => setImportance(e.target.value as 'High' | 'Medium' | 'Low')}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>

            {/* --- Natural Language Task Section --- */}
<div className="bg-slate-900 rounded-xl p-6 border border-slate-700 space-y-4">
  {/* Natural Language Entry */}
  <div>
    <label className="block text-sm font-medium text-slate-300 mb-2">Natural Language Entry</label>
    <textarea
      value={nlTask}
      onChange={(e) => setNlTask(e.target.value)}
      rows={3}
      className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
      placeholder="Describe your task in natural language..."
    />
  </div>


{/* Tabs */}
<div className="mt-6">
  <div className="flex border-b border-slate-600">
    {/* Warning Tab */}
    <button
      type="button"
      onClick={() => setActiveTab('warning')}
      className={`flex items-center space-x-2 px-4 py-2 font-medium ${
        activeTab === 'warning'
          ? 'text-orange-400 border-b-2 border-orange-400'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      <AlertTriangle className="w-4 h-4" />
      <span>Warning</span>
    </button>

    {/* Suggestions Tab */}
    <button
      type="button"
      onClick={() => setActiveTab('suggestions')}
      className={`flex items-center space-x-2 px-4 py-2 font-medium ${
        activeTab === 'suggestions'
          ? 'text-emerald-400 border-b-2 border-emerald-400'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      <Lightbulb className="w-4 h-4" />
      <span>Suggestions</span>
    </button>

    {/* Tasks Summary Tab */}
    <button
      type="button"
      onClick={() => setActiveTab('summary')}
      className={`flex items-center space-x-2 px-4 py-2 font-medium ${
        activeTab === 'summary'
          ? 'text-blue-400 border-b-2 border-blue-400'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      <ClipboardCheck className="w-4 h-4" />
      <span>Tasks Summary</span>
    </button>
  </div>

  {/* Tab Content */}
  <div className="mt-4">
  <textarea
  value={
    activeTab === 'warning'
      ? warningMsg
      : activeTab === 'suggestions'
      ? suggestionMsg
      : Array.isArray(tasksSummaryMsg) && tasksSummaryMsg.length > 0
      ? tasksSummaryMsg
          .map(
            (task: any) =>
              `Task Name: ${task.TaskName} | Duration: ${task.Duration} | Arrival: ${task.arrivaltime} ${task.arrivaldate} | Deadline: ${task.deadlinetime} ${task.deadlinedate} | Importance: ${task.importance}`
          )
          .join('\n\n') // Each task on a new line
      : 'No tasks summary available.'
  }
  readOnly
  rows={Math.max(3, Array.isArray(tasksSummaryMsg) ? tasksSummaryMsg.length : 3)}
  className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-300"
/>

  </div>
</div>


  {/* Natural Language Response */}
  <div>
    <label className="block text-sm font-medium text-slate-300 mb-2">Natural Language Response</label>
    <textarea
      value={nlResponse}
      onChange={(e) => setNlResponse(e.target.value)}
      placeholder="Enter your response for suggestions"
      rows={2}
      className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
    />
  </div>
  <button
    onClick={() => handleValidateTask(nlTask, nlResponse, warningMsg, suggestionMsg, tasksSummaryMsg)}
    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
  >
    Validate
  </button>
</div>

            {/* Entry Type Selection */}
<div className="mb-4">
  <span className="block text-sm font-medium text-slate-300 mb-2">Select Entry Type</span>
  <div className="flex space-x-6">
    <label className="flex items-center space-x-2">
      <input
        type="radio"
        name="entryType"
        value="nl"
        checked={entryType === 'nl'}
        onChange={() => setEntryType('nl')}
        className="accent-emerald-500"
      />
      <span className="text-slate-300">Natural Language Entry</span>
    </label>

    <label className="flex items-center space-x-2">
      <input
        type="radio"
        name="entryType"
        value="form"
        checked={entryType === 'form'}
        onChange={() => setEntryType('form')}
        className="accent-emerald-500"
      />
      <span className="text-slate-300">Form Entry</span>
    </label>
  </div>
</div>

            <button
              onClick={() => handleAddTask(entryType)}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 shadow-lg"
            >
              Final Validation and Add Tasks
            </button>
          </div>
        </div>

        {/* Right Panel - Task List & Scheduler */}
        <div className="space-y-6">
          {/* Task List */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h3 className="text-lg font-bold mb-4 text-emerald-400">Task List</h3>
            
            <div className="max-h-64 overflow-auto mb-4">
              <table className="w-full text-sm">
                <thead className="bg-slate-700">
                  <tr>
                    <th className="px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Task Name</th>
                    <th className="px-3 py-2 text-left">Duration</th>
                    <th className="px-3 py-2 text-left">Deadline</th>
                    <th className="px-3 py-2 text-left">Importance</th>
                    <th className="px-3 py-2 text-left">Arrival Time</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => (
                    <tr key={task.id} className="border-b border-slate-600">
                      <td className="px-3 py-2">{task.id}</td>
                      <td className="px-3 py-2">{task.taskName}</td>
                      <td className="px-3 py-2">{task.duration}h</td>
                      <td className="px-3 py-2">{task.deadlineTime.hrs}h, {task.deadlineTime.date}</td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          task.importance === 'High' ? 'bg-red-600' :
                          task.importance === 'Medium' ? 'bg-yellow-600' : 'bg-green-600'
                        }`}>
                          {task.importance}
                        </span>
                      </td>
                      <td className="px-3 py-2">{task.arrivalTime.hrs}h, {task.arrivalTime.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {tasks.length === 0 && (
                <div className="text-center py-8 text-slate-400">No tasks added yet</div>
              )}
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleDeleteAllTasks}
                  className="flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete All Tasks</span>
                </button>
                <button
                  onClick={handleExportTasks}
                  className="flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                >
                  <Download className="w-4 h-4" />
                  <span>Export JSON</span>
                </button>
              </div>
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={deleteIds}
                  onChange={(e) => setDeleteIds(e.target.value)}
                  placeholder="Task IDs (comma-separated)"
                  className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
                <button
                  onClick={handleDeleteSpecificTasks}
                  className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                >
                  Delete
                </button>
              </div>

              <div>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleImportTasks}
                  className="hidden"
                  id="import-tasks"
                />
                <label
                  htmlFor="import-tasks"
                  className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg cursor-pointer transition-colors duration-200"
                >
                  <Upload className="w-4 h-4" />
                  <span>Import Tasks JSON</span>
                </label>
              </div>
            </div>
          </div>

          {/* Scheduler Box */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h3 className="text-lg font-bold mb-4 text-emerald-400">Scheduler Controls</h3>
            
            <div className="space-y-4">
              {/* Manual Scheduler */}
              <div className="bg-slate-700 p-4 rounded-lg">
                <h4 className="font-medium mb-3">Manual Scheduler</h4>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">Algorithm</label>
                    <select
                      value={manualAlgo}
                      onChange={(e) => setManualAlgo(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="FCFS">First Come First Serve</option>
                      <option value="SJF">Shortest Job First</option>
                      <option value="SRTF">Shortest Remaining Time First</option>
                      <option value="RR">Round Robin</option>
                      <option value="PS">Priority Scheduling</option>
                      <option value="EDF">Earliest Deadline First</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">Quantum</label>
                    <input
                      type="text"
                      value={quantum}
                      onChange={(e) => setQuantum(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
                <button
                  onClick={() => handleRunManualScheduler(tasks,manualAlgo,quantum)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                >
                  Run Manual Scheduler
                </button>
              </div>

              {/* AI Suggested Scheduler */}
              <div className="bg-slate-700 p-4 rounded-lg">
                <h4 className="font-medium mb-3">AI Suggested Scheduler</h4>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">AI Algorithm</label>
                    <input
                      type="text"
                      value={aiAlgo}
                      readOnly
                      className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-slate-300"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">AI Quantum</label>
                    <input
                      type="text"
                      value={aiQuantum}
                      readOnly
                      className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-slate-300"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => handleAISuggest(tasks)}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                  >
                    AI Suggest
                  </button>
                  <button
                    onClick={() => handleRunAIScheduler(tasks,aiAlgo,aiQuantum)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                  >
                    Run AI Scheduler
                  </button>
                </div>
              </div>

              <button
                onClick={() => navigate('schedule-viz')}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200"
              >
                Next → Schedule Visualization
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}