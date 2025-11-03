import React, { useState } from 'react';
import { Download, Play } from 'lucide-react';
import { NotificationType } from '../types';
import { apiCall } from '../utils/api';
import { API_URL } from '../utils/backend_config';
import GanttChart from './GanttChart';   // adjust path if different

interface ScheduleVisualizationSectionProps {
  manualSchedule: any[];
  aiSchedule: any[];
  showNotification: (message: string, type: NotificationType) => void;
  manualAlgo?: string;
  quantum?: string;
  aiAlgo?: string;
  aiQuantum?: string;
  navigate: React.Dispatch<React.SetStateAction<'task-input' | 'schedule-viz' | 'ai-interaction'>>;
  agentAlgo?: string;
  agentQuantum?: string;
  agentSchedule?: any[];
  setAgentAlgo?: React.Dispatch<React.SetStateAction<string>>;
  setAgentQuantum?: React.Dispatch<React.SetStateAction<string>>;
  setAgentSchedule?: React.Dispatch<React.SetStateAction<any[]>>;
  resetMemorySchedule: any[];
  setResetMemorySchedule: React.Dispatch<React.SetStateAction<any[]>>;
}

export default function ScheduleVisualizationSection({ showNotification, manualSchedule, aiSchedule, manualAlgo, quantum, aiAlgo, aiQuantum, navigate, agentAlgo, agentQuantum, agentSchedule, setAgentAlgo, setAgentQuantum, setAgentSchedule, resetMemorySchedule, setResetMemorySchedule }: ScheduleVisualizationSectionProps) {
  const [finalChoice, setFinalChoice] = useState<'manual' | 'AI'>('manual');

  const handleDownloadJPEG = async (type: 'manual' | 'ai') => {
    const success = await apiCall(`/api/download${type}Chart`);
    if (success) {
      showNotification(`${type === 'manual' ? 'Manual' : 'AI'} chart downloaded successfully`, 'success');
    } else {
      showNotification(`Failed to download ${type} chart`, 'error');
    }
  };

  const handleSubmitFinalSelection = async (finalChoice: 'manual' | 'AI') => {
    const [success, data] = await apiCall(API_URL + '/api/rl_feedback','POST', { choice: finalChoice });
    if (success) {
      showNotification('Final selection submitted successfully', 'success');
    } else {
      showNotification('Failed to submit final selection', 'error');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-emerald-400 mb-2">Schedule Visualization</h2>
        <p className="text-slate-400">Compare manual and AI-generated scheduling algorithms</p>
      </div>

      {/* Manual Scheduler Visualization */}
      <div className="bg-slate-800 rounded-xl border border-slate-700">
        <div className="p-6 border-b border-slate-700">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold text-blue-400">Manual Scheduler Visualization</h3>
            <button
              onClick={() => handleDownloadJPEG('manual')}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              <Download className="w-4 h-4" />
              <span>Download as JPEG</span>
            </button>
          </div>
        </div>
        
        <div className="bg-slate-900 flex items-center justify-center py-4">
      {/* Replace the existing content with the GanttChart */}
      {manualSchedule && manualSchedule.length > 0 ? (
        <GanttChart tasks={manualSchedule} algo={manualAlgo} tq={quantum} />
      ) : (
        <div className="text-center">
          <p className="text-slate-500">No schedule data available</p>
        </div>
      )}
      
      </div>
      </div>

      {/* AI Suggested Scheduler Visualization */}
      <div className="bg-slate-800 rounded-xl border border-slate-700">
        <div className="p-6 border-b border-slate-700">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold text-emerald-400">AI Scheduler Visualization</h3>
            <button
              onClick={() => handleDownloadJPEG('ai')}
              className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              <Download className="w-4 h-4" />
              <span>Download as JPEG</span>
            </button>
          </div>
        </div>
        
        <div className="bg-slate-900 flex items-center justify-center py-4">
      {/* Replace the existing content with the GanttChart */}
      {aiSchedule && aiSchedule.length > 0 ? (
        <GanttChart tasks={aiSchedule} algo={aiAlgo} tq={aiQuantum} />
      ) : (
        <div className="text-center">
          <p className="text-slate-500">No schedule data available</p>
        </div>
      )}
      
    </div>
    

      </div>

      {/* Final Selection Controls */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h3 className="text-xl font-bold text-orange-400 mb-6">Final Selection</h3>
        
        <div className="space-y-6">
          <div className="flex justify-center space-x-8">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="radio"
                name="finalChoice"
                value="manual"
                checked={finalChoice === 'manual'}
                onChange={(e) => setFinalChoice(e.target.value as 'manual' | 'AI')}
                className="w-5 h-5 text-blue-600 bg-slate-700 border-slate-600 focus:ring-blue-500 focus:ring-2"
              />
              <span className="text-lg font-medium text-blue-400">Manual Scheduler</span>
            </label>
            
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="radio"
                name="finalChoice"
                value="AI"
                checked={finalChoice === 'AI'}
                onChange={(e) => setFinalChoice(e.target.value as 'manual' | 'AI')}
                className="w-5 h-5 text-emerald-600 bg-slate-700 border-slate-600 focus:ring-emerald-500 focus:ring-2"
              />
              <span className="text-lg font-medium text-emerald-400">AI Suggested Scheduler</span>
            </label>
          </div>

          <div className="text-center">
            <button
              onClick={()=>{
                handleSubmitFinalSelection(finalChoice); 
                if (finalChoice === 'manual') {
                  setAgentAlgo?.(manualAlgo || '');
                  setAgentQuantum?.(quantum || '');
                  setAgentSchedule?.(manualSchedule || []);
                  setResetMemorySchedule(manualSchedule)
                } else {
                  setAgentAlgo?.(aiAlgo || '');
                  setAgentQuantum?.(aiQuantum || '');
                  setAgentSchedule?.(aiSchedule || []);
                  setResetMemorySchedule(aiSchedule)
                }
                navigate('ai-interaction');
              }
            }
              className="bg-orange-600 hover:bg-orange-700 text-white font-bold py-3 px-8 rounded-lg transition-colors duration-200 shadow-lg transform hover:scale-105"
            >
              Submit & Head to AI Interaction
            </button>
          </div>

          <div className="text-center text-sm text-slate-400">
            Selected: <span className={`font-medium ${finalChoice === 'manual' ? 'text-blue-400' : 'text-emerald-400'}`}>
              {finalChoice === 'manual' ? 'Manual Scheduler' : 'AI Suggested Scheduler'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}