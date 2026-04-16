
export interface TimeSlotRow {
  id: number;
  slot: number;
  name: string;
  start_time: string;
  end_time: string;
}

export interface LessonRow {
  id: string;
  day: string;
  slot: number;
  subject: string;
  group: string;
  teacher: string;
  room: string;
  scheduleItemId?: number;
  fixed?: boolean;
}

export interface LessonDraft {
  subject: string;
  group: string;
  teacher: string;
  room: string;
  slot: number;
  day: string;
  // добавь остальные поля по необходимости
}

