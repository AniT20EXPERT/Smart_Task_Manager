export interface Task {
  id: number;
  taskName: string;
  duration: number;
  arrivalTime: {
    hrs: number;
    date: string;
  };
  deadlineTime: {
    hrs: number;
    date: string;
  };
  importance: 'High' | 'Medium' | 'Low';
}

export type NotificationType = 'success' | 'error' | 'info';