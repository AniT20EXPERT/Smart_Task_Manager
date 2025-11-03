import React from 'react';

interface Task {
  task: string;
  start: number;
  end: number;
  date: string;
}

interface GanttChartProps {
  tasks: Task[];
  algo?: string;
  tq?: string;
  height?: number;
}

const GanttChart: React.FC<GanttChartProps> = ({ tasks, algo, tq, height = 320 }) => {
  // Group tasks by date
  const tasksByDate = tasks.reduce((acc, task) => {
    if (!acc[task.date]) {
      acc[task.date] = [];
    }
    acc[task.date].push(task);
    return acc;
  }, {} as Record<string, Task[]>);
  
  const sortedDates = Object.keys(tasksByDate).sort();
  
  // Define colors for tasks (cycling through a palette)
  const colorPalette = [
    'bg-blue-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-teal-500',
    'bg-cyan-500',
    'bg-green-500',
    'bg-orange-500',
  ];
  
  // Create a mapping of task names to colors
  const taskColorMap: Record<string, string> = {};
  const uniqueTaskNames = [...new Set(tasks.map(t => t.task))];
  uniqueTaskNames.forEach((taskName, index) => {
    taskColorMap[taskName] = colorPalette[index % colorPalette.length];
  });
  
  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };
  
  return (
    <div className="w-full h-full bg-slate-900 p-3 rounded-lg overflow-auto">
      <div className="min-w-[700px]">
        {/* Header */}
        <div className="mb-3">
          <h3 className="text-base font-semibold text-slate-200">Task Schedule</h3>
          {algo && <p className="text-xs text-slate-400">Algorithm: {algo}</p>}
          {tq && <p className="text-xs text-slate-400">TQ: {tq}</p>}
        </div>
        
        {/* Date Sections */}
        {sortedDates.map((date, dateIndex) => {
          const dateTasks = tasksByDate[date];
          const maxEnd = Math.max(...dateTasks.map(t => t.end));
          const minStart = Math.min(...dateTasks.map(t => t.start));
          const totalDuration = maxEnd - minStart;
          
          // Group overlapping tasks within the same date
          const getTaskRow = (task: Task, index: number): number => {
            const overlappingTasks = dateTasks.slice(0, index).filter(
              t => !(t.end <= task.start || t.start >= task.end)
            );
            return overlappingTasks.length;
          };
          
          const maxRows = Math.max(...dateTasks.map((task, i) => getTaskRow(task, i))) + 1;
          const rowHeight = 60;
          const chartHeight = Math.max(maxRows * (rowHeight + 8), 150);
          
          // Generate time markers
          const timeMarkers = [];
          for (let i = minStart; i <= maxEnd; i++) {
            timeMarkers.push(i);
          }
          
          return (
            <div key={date} className="mb-4">
              {/* Date Header */}
              <div className="flex items-center mb-2">
                <div className="bg-slate-800 px-3 py-1.5 rounded-md">
                  <h4 className="text-sm font-semibold text-slate-200">{formatDate(date)}</h4>
                  <p className="text-xs text-slate-400">{date}</p>
                </div>
              </div>
              
              {/* Chart Container */}
              <div className="relative bg-slate-800 rounded-lg p-3" style={{ minHeight: `${chartHeight + 60}px` }}>
                {/* Time axis */}
                <div className="absolute top-0 left-0 right-0 h-8 border-b border-slate-700">
                  <div className="relative h-full">
                    {timeMarkers.map((time) => (
                      <div
                        key={time}
                        className="absolute flex flex-col items-center"
                        style={{
                          left: `${((time - minStart) / totalDuration) * 100}%`,
                          transform: 'translateX(-50%)',
                        }}
                      >
                        <span className="text-xs text-slate-400 font-medium">
                          {time}h
                        </span>
                        <div className="w-px h-1 bg-slate-600 mt-1"></div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Grid lines */}
                <div className="absolute top-8 left-0 right-0 bottom-0 pointer-events-none">
                  {timeMarkers.map((time) => (
                    <div
                      key={`grid-${time}`}
                      className="absolute top-0 bottom-0 w-px bg-slate-700 opacity-30"
                      style={{
                        left: `${((time - minStart) / totalDuration) * 100}%`,
                      }}
                    ></div>
                  ))}
                </div>
                
                {/* Tasks */}
                <div className="relative mt-10" style={{ minHeight: `${chartHeight}px` }}>
                  {dateTasks.map((task, index) => {
                    const duration = task.end - task.start;
                    const startPercent = ((task.start - minStart) / totalDuration) * 100;
                    const widthPercent = (duration / totalDuration) * 100;
                    const row = getTaskRow(task, index);
                    const color = taskColorMap[task.task];
                    
                    return (
                      <div
                        key={index}
                        className={`absolute ${color} rounded-md shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 cursor-pointer group`}
                        style={{
                          left: `${startPercent}%`,
                          width: `${widthPercent}%`,
                          height: `${rowHeight}px`,
                          top: `${row * (rowHeight + 8)}px`,
                          minWidth: '80px',
                        }}
                      >
                        <div className="flex items-center justify-between h-full px-3 py-2 relative">
                          <div className="flex-1 min-w-0 pr-2 overflow-hidden">
                            <p className="text-white text-sm font-medium leading-tight line-clamp-2">
                              {task.task}
                            </p>
                            <p className="text-white text-xs opacity-80 mt-0.5">
                              {task.start}h - {task.end}h
                            </p>
                          </div>
                          
                          {/* Duration badge */}
                          <div className="ml-2 bg-white bg-opacity-20 rounded px-2 py-1 flex-shrink-0">
                            <span className="text-xs text-white font-semibold">
                              {duration}h
                            </span>
                          </div>
                          
                          {/* Hover tooltip */}
                          <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-slate-700 text-white px-3 py-2 rounded-md text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none shadow-xl z-10">
                            <div className="font-semibold">{task.task}</div>
                            <div>Duration: {duration} hour{duration > 1 ? 's' : ''}</div>
                            <div>Time: {task.start}h - {task.end}h</div>
                            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-slate-700 rotate-45"></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                {/* Legend */}
                <div className="mt-3 pt-2 border-t border-slate-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center text-xs text-slate-400">
                        <div className="w-3 h-3 bg-blue-500 rounded-sm mr-2"></div>
                        <span>Task Block</span>
                      </div>
                      <div className="flex items-center text-xs text-slate-400">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Time in hours</span>
                      </div>
                    </div>
                    <div className="text-xs text-slate-500">
                      Duration: {totalDuration}h ({dateTasks.length} task{dateTasks.length > 1 ? 's' : ''})
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GanttChart;