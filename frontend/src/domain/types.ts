import type { InjectionKey, Ref } from "vue";

export type Building = {
  id: string;
  name: string;
  address: string;
};

export type Faculty = {
  id: string;
  name: string;
  shortName: string;
};

export type Department = {
  id: string;
  name: string;
  facultyId: string;
};

/** Аудитория */
export type Auditorium = {
  id: string;
  number: string;
  buildingId: string;
  capacity: number | null;
  note: string;
};

export type Group = {
  id: string;
  name: string;
  facultyId: string;
};

export type Teacher = {
  id: string;
  lastName: string;
  firstName: string;
  patronymic: string;
  departmentId: string;
};

export type Subject = {
  id: string;
  name: string;
  code: string;
};

export type TimeSlotRow = {
  id: string;
  slot: number;
  time: string;
};

/** Запись академического календаря */
export type CalendarEntry = {
  id: string;
  date: string;
  kind: "holiday" | "transfer" | "exam" | "other";
  title: string;
};

export type UserType = {
  id: string;
  name: string;
  description: string;
};

export type Permission = {
  id: string;
  key: string;
  label: string;
};

export type Role = {
  id: string;
  name: string;
  userTypeId: string;
  permissionIds: string[];
};

export type AppUser = {
  id: string;
  login: string;
  displayName: string;
  email: string;
  roleId: string;
  active: boolean;
};

export type CatalogState = {
  weekDays: Ref<string[]>;
  timeSlots: Ref<TimeSlotRow[]>;
  buildings: Ref<Building[]>;
  faculties: Ref<Faculty[]>;
  departments: Ref<Department[]>;
  auditoriums: Ref<Auditorium[]>;
  groups: Ref<Group[]>;
  teachers: Ref<Teacher[]>;
  subjects: Ref<Subject[]>;
  calendar: Ref<CalendarEntry[]>;
  userTypes: Ref<UserType[]>;
  permissions: Ref<Permission[]>;
  roles: Ref<Role[]>;
  users: Ref<AppUser[]>;
};

export const catalogStateKey: InjectionKey<CatalogState> = Symbol("catalogState");

export function teacherDisplayName(t: Teacher): string {
  const parts = [t.lastName, t.firstName, t.patronymic].map((s) => s.trim()).filter(Boolean);
  return parts.join(" ");
}
