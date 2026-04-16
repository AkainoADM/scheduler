import type {
  AppUser,
  Auditorium,
  Building,
  CalendarEntry,
  Department,
  Faculty,
  Group,
  Permission,
  Role,
  Subject,
  Teacher,
  TimeSlotRow,
  UserType,
} from "./types";
import { teacherDisplayName } from "./types";

export const INITIAL_WEEK_DAYS = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
];

export const INITIAL_TIME_SLOTS: TimeSlotRow[] = [
  { id: "ts1", slot: 1, time: "08:00 - 09:30" },
  { id: "ts2", slot: 2, time: "09:40 - 11:10" },
  { id: "ts3", slot: 3, time: "11:20 - 12:50" },
  { id: "ts4", slot: 4, time: "13:20 - 14:50" },
  { id: "ts5", slot: 5, time: "15:00 - 16:30" },
  { id: "ts6", slot: 6, time: "16:40 - 18:10" },
];

const GROUP_NAMES: string[] = [
  "130Б",
  "130М",
  "131М",
  "132Б",
  "133Б",
  "133Б-А",
  "133Б-Б",
  "134Б",
  "135Б-А",
  "135Б-Б",
  "136Б",
  "230Б",
  "230М",
  "231Б",
  "231М",
  "232Б",
  "233Б",
  "233Б-А",
  "233Б-Б",
  "234Б",
  "235Б-А",
  "235Б-Б",
  "236Б",
  "3-17Б",
  "3-27Б",
  "330Б",
  "331Б",
  "332Б",
  "332Б-А",
  "332Б-Б",
  "333Б-А",
  "333Б-Б",
  "334Б",
  "334Б-А",
  "334Б-Б",
  "334Б-В",
  "335Б-А",
  "335Б-Б",
  "335Б-В",
  "336Б",
  "3-37Б",
  "3-47Б",
  "3-57Б",
  "430Б",
  "431Б",
  "431Б-А",
  "432Б",
  "432Б-А",
  "432Б-Б",
  "433Б-А",
  "433Б-Б",
  "434Б-А",
  "434Б-Б",
  "434Б-В",
  "435Б",
  "435Б-А",
  "435Б-Б",
  "436Б-А",
  "437Б",
  "532Б-А",
  "532Б-Б",
  "533Б",
  "533Б-А",
  "533Б-Б",
  "534Б",
  "534Б-А",
  "534Б-Б",
  "534Б-В",
];

export function seedFaculties(): Faculty[] {
  return [
    { id: "f1", name: "Факультет математики и информационных технологий", shortName: "ФМиИТ" },
    { id: "f2", name: "Инженерно-педагогический факультет", shortName: "ИПФ" },
  ];
}

export function seedBuildings(): Building[] {
  return [
    { id: "b1", name: "Корпус А", address: "ул. Примерная, 1" },
    { id: "b2", name: "Корпус Б", address: "ул. Примерная, 3" },
    { id: "b3", name: "Корпус В", address: "ул. Примерная, 5" },
  ];
}

export function seedDepartments(): Department[] {
  return [
    { id: "d1", name: "Кафедра высшей математики", facultyId: "f1" },
    { id: "d2", name: "Кафедра информатики", facultyId: "f1" },
    { id: "d3", name: "Кафедра педагогики", facultyId: "f2" },
  ];
}

export function seedGroups(facultyId: string): Group[] {
  return GROUP_NAMES.map((name, i) => ({
    id: `g${i + 1}`,
    name,
    facultyId,
  }));
}

const teacherSeeds: Omit<Teacher, "id">[] = [
  { lastName: "Гордиевских", firstName: "А.В.", patronymic: "", departmentId: "d1" },
  { lastName: "Злобина", firstName: "Е.П.", patronymic: "", departmentId: "d1" },
  { lastName: "Слинкин", firstName: "И.А.", patronymic: "", departmentId: "d2" },
  { lastName: "Ефимов", firstName: "М.С.", patronymic: "", departmentId: "d3" },
  { lastName: "Козловских", firstName: "Н.Н.", patronymic: "", departmentId: "d2" },
  { lastName: "Оболдина", firstName: "Т.В.", patronymic: "", departmentId: "d1" },
  { lastName: "Светоносова", firstName: "О.И.", patronymic: "", departmentId: "d3" },
  { lastName: "Волгуснова", firstName: "Ю.А.", patronymic: "", departmentId: "d3" },
  { lastName: "Пирогов", firstName: "С.В.", patronymic: "", departmentId: "d2" },
];

export function seedTeachers(): Teacher[] {
  return teacherSeeds.map((t, i) => ({
    id: `t${i + 1}`,
    ...t,
  }));
}

export function seedSubjects(): Subject[] {
  return [
    { id: "s1", name: "Математический анализ", code: "МА.101" },
    { id: "s2", name: "Физика", code: "ФИЗ.101" },
    { id: "s3", name: "Программирование", code: "ПР.201" },
    { id: "s4", name: "Английский язык", code: "АНГ.101" },
    { id: "s5", name: "Алгебра", code: "АЛГ.101" },
    { id: "s6", name: "Педагогика", code: "ПЕД.301" },
    { id: "s7", name: "Психология", code: "ПСХ.201" },
    { id: "s8", name: "Информационные системы", code: "ИС.401" },
    { id: "s9", name: "Микроэлектроника", code: "МЭ.301" },
    { id: "s10", name: "Вычислительная математика", code: "ВМ.201" },
  ];
}

export function seedAuditoriums(): Auditorium[] {
  return [
    { id: "a1", number: "233А", buildingId: "b1", capacity: 30, note: "" },
    { id: "a2", number: "201Б", buildingId: "b2", capacity: 25, note: "" },
    { id: "a3", number: "219А", buildingId: "b1", capacity: 24, note: "Компьютерный класс" },
    { id: "a4", number: "130А", buildingId: "b1", capacity: 20, note: "" },
    { id: "a5", number: "201В", buildingId: "b3", capacity: 28, note: "" },
    { id: "a6", number: "204Б", buildingId: "b2", capacity: 30, note: "" },
    { id: "a7", number: "316В", buildingId: "b3", capacity: 22, note: "" },
    { id: "a8", number: "318В", buildingId: "b3", capacity: 22, note: "" },
    { id: "a9", number: "235А", buildingId: "b1", capacity: 26, note: "" },
    { id: "a10", number: "139А", buildingId: "b1", capacity: 18, note: "" },
  ];
}

export function seedCalendar(): CalendarEntry[] {
  return [
    { id: "c1", date: "2026-09-01", kind: "other", title: "Начало осеннего семестра" },
    { id: "c2", date: "2026-11-04", kind: "holiday", title: "Выходной" },
    { id: "c3", date: "2026-12-25", kind: "holiday", title: "Зимние каникулы" },
  ];
}

export function seedUserTypes(): UserType[] {
  return [
    { id: "ut1", name: "Студент", description: "Просмотр расписания" },
    { id: "ut2", name: "Преподаватель", description: "Просмотр и личное расписание" },
    { id: "ut3", name: "Диспетчер", description: "Редактирование расписания" },
    { id: "ut4", name: "Администратор", description: "Полный доступ" },
  ];
}

export function seedPermissions(): Permission[] {
  return [
    { id: "p1", key: "schedule.view", label: "Просмотр расписания" },
    { id: "p2", key: "schedule.edit", label: "Редактирование расписания" },
    { id: "p3", key: "directories.read", label: "Просмотр справочников" },
    { id: "p4", key: "directories.manage", label: "Управление справочниками" },
    { id: "p5", key: "users.read", label: "Просмотр пользователей" },
    { id: "p6", key: "users.manage", label: "Управление пользователями и ролями" },
  ];
}

export function seedRoles(): Role[] {
  return [
    {
      id: "r1",
      name: "Студент",
      userTypeId: "ut1",
      permissionIds: ["p1"],
    },
    {
      id: "r2",
      name: "Читатель расписания",
      userTypeId: "ut1",
      permissionIds: ["p1", "p3"],
    },
    {
      id: "r3",
      name: "Составитель расписания",
      userTypeId: "ut3",
      permissionIds: ["p1", "p2", "p3", "p4"],
    },
    {
      id: "r4",
      name: "Системный администратор",
      userTypeId: "ut4",
      permissionIds: ["p1", "p2", "p3", "p4", "p5", "p6"],
    },
  ];
}

export function seedUsers(): AppUser[] {
  return [
    {
      id: "u1",
      login: "admin",
      displayName: "Администратор системы",
      email: "admin@example.edu",
      roleId: "r4",
      active: true,
    },
    {
      id: "u2",
      login: "dispatcher1",
      displayName: "Иванова Анна Петровна",
      email: "ivanova@example.edu",
      roleId: "r3",
      active: true,
    },
  ];
}

/** Имена групп для начального расписания (первый факультет) */
export function seedGroupNamesList(): string[] {
  return [...GROUP_NAMES];
}

/** Подсказки: ФИО преподавателей из справочника */
export function seedTeacherNameList(): string[] {
  return seedTeachers().map(teacherDisplayName);
}

/** Номера аудиторий */
export function seedAuditoriumNumberList(): string[] {
  return seedAuditoriums().map((a) => a.number);
}
