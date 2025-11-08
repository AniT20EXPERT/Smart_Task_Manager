import React, { useState } from 'react';
import { Download, RotateCcw, Send, Bot, User } from 'lucide-react';
import { Task, NotificationType } from '../types';
import { apiCall } from '../utils/api';
import GanttChart from './GanttChart';
import { API_URL } from '../utils/backend_config';
interface AIInteractionSectionProps {
  tasks: Task[];
  showNotification: (message: string, type: NotificationType) => void;
  agentAlgo: string;
  agentQuantum: string;
  agentSchedule: any[];
  resetMemorySchedule: any[];
  setAgentSchedule: React.Dispatch<React.SetStateAction<any[]>>;
}

interface ChatMessage {
  id: number;
  type: 'user' | 'ai';
  message: string;
  timestamp: Date;
}

export default function AIInteractionSection({ tasks, showNotification, agentAlgo, agentQuantum, agentSchedule, resetMemorySchedule, setAgentSchedule }: AIInteractionSectionProps) {
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      type: 'ai',
      message: 'Hello! I\'m your AI scheduling assistant. How can I help you optimize your task schedule today?',
      timestamp: new Date()
    }
  ]);

  const handleResetChart = async () => {
    const success = await apiCall('/api/resetChart');
    if (success) {
      setAgentSchedule(resetMemorySchedule);
      showNotification('Timeline chart reset successfully', 'success');
    } else {
      showNotification('Failed to reset chart', 'error');
    }
  };

  const handleDownloadChart = async () => {
    const success = await apiCall('/api/downloadChart');
    if (success) {
      // setAgentSchedule(["empty","empty"]);
      showNotification('Chart downloaded successfully', 'success');
    } else {
      showNotification('Failed to download chart', 'error');
    }
  };
  const [chatResponse, setChatResponse] = useState('');
  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      message: chatInput,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');

    // Call API
    console.log(agentSchedule);
    const [success, data] = await apiCall(API_URL + '/api/chat','POST', { user_prompt: chatInput, task_list: agentSchedule});
    if (success) {
      //set agentschedule
      setAgentSchedule(data.task_list);
      console.log("success chat response called!")
      console.log(agentSchedule);
      setChatResponse(data.chat_response);
      // Add AI response
      const aiMessage: ChatMessage = {
        id: Date.now() + 1,
        type: 'ai',
        message: data.chat_response,
        timestamp: new Date()
      };
      

      setTimeout(() => {
        setChatMessages(prev => [...prev, aiMessage]);
      }, 1000);

      showNotification('Message sent successfully', 'success');
    } else {
      showNotification('Failed to send message', 'error');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="p-6 space-y-6 h-full">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-emerald-400 mb-2">AI Interaction Panel</h2>
        <p className="text-slate-400">Dynamic timeline visualization and intelligent chat assistance</p>
      </div>

      {/* Timeline Visualizer */}
      <div className="bg-slate-800 rounded-xl border border-slate-700">
        <div className="p-6 border-b border-slate-700">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold text-purple-400">Dynamic Timeline Visualizer</h3>
            <div className="flex space-x-3">
              <button
                onClick={handleResetChart}
                className="flex items-center space-x-2 bg-slate-600 hover:bg-slate-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Reset</span>
              </button>
              <button
                onClick={handleDownloadChart}
                className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                <Download className="w-4 h-4" />
                <span>Download JPEG</span>
              </button>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-900 flex items-center justify-center py-4">
      {/* Replace the existing content with the GanttChart */}
      {agentSchedule && agentSchedule.length > 0 ? (
        <GanttChart tasks={agentSchedule} algo={agentAlgo} tq={agentQuantum} />
      ) : (
        <div className="text-center">
          <p className="text-slate-500">No schedule data available</p>
        </div>
      )}
      
      </div>
      </div>

      {/* Chatbot Area */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 h-96 flex flex-col">
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-lg font-bold text-emerald-400">AI Assistant Chat</h3>
        </div>
        
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {chatMessages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex items-start space-x-3 max-w-3/4 ${
                  message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-blue-600' : 'bg-emerald-600'
                  }`}
                >
                  {message.type === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>
                <div
                  className={`px-4 py-2 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-100'
                  }`}
                >
                  <p className="text-sm">{message.message}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Chat Input */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex space-x-3">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message to the AI assistant..."
              className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
            <button
              onClick={handleSendMessage}
              disabled={!chatInput.trim()}
              className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}