<script setup lang="ts">
import { computed, inject, ref } from "vue";
import type {
  Auditorium,
  Building,
  CalendarEntry,
  Department,
  Faculty,
  Group,
  Subject,
  Teacher,
  TimeSlotRow,
  UserType,
} from "../../domain/types";
import { catalogStateKey, teacherDisplayName } from "../../domain/types";
import { createEntityId } from "../../utils/id";

type SectionId =
  | "faculties"
  | "buildings"
  | "departments"
  | "groups"
  | "teachers"
  | "subjects"
  | "auditoriums"
  | "timeSlots"
  | "calendar"
  | "userTypes";

const catalog = inject(catalogStateKey)!;

const active = ref<SectionId>("faculties");

const navItems: { id: SectionId; label: string }[] = [
  { id: "faculties", label: "Факультеты" },
  { id: "buildings", label: "Здания" },
  { id: "departments", label: "Подразделения" },
  { id: "groups", label: "Группы" },
  { id: "teachers", label: "Преподаватели" },
  { id: "subjects", label: "Предметы" },
  { id: "auditoriums", label: "Аудитории" },
  { id: "timeSlots", label: "Временные слоты" },
  { id: "calendar", label: "Календарь" },
  { id: "userTypes", label: "Типы пользователей" },
];

const facultyById = computed(() => new Map(catalog.faculties.value.map((f) => [f.id, f])));
const buildingById = computed(() => new Map(catalog.buildings.value.map((b) => [b.id, b])));
const departmentById = computed(() => new Map(catalog.departments.value.map((d) => [d.id, d])));

function confirmDelete(label: string): boolean {
  return window.confirm(`Удалить «${label}»?`);
}

const facultyDraft = ref<Faculty | null>(null);
function newFaculty(): void {
  facultyDraft.value = { id: "", name: "", shortName: "" };
}
function editFaculty(row: Faculty): void {
  facultyDraft.value = { ...row };
}
function saveFaculty(): void {
  const d = facultyDraft.value;
  if (!d || !d.name.trim()) return;
  if (d.id) {
    catalog.faculties.value = catalog.faculties.value.map((f) =>
      f.id === d.id ? { ...d, name: d.name.trim(), shortName: d.shortName.trim() } : f,
    );
  } else {
    catalog.faculties.value = [
      ...catalog.faculties.value,
      { ...d, id: createEntityId(), name: d.name.trim(), shortName: d.shortName.trim() },
    ];
  }
  facultyDraft.value = null;
}
function cancelFaculty(): void {
  facultyDraft.value = null;
}
function removeFaculty(id: string): void {
  const f = catalog.faculties.value.find((x) => x.id === id);
  if (!f || !confirmDelete(f.name)) return;
  catalog.faculties.value = catalog.faculties.value.filter((x) => x.id !== id);
}

const buildingDraft = ref<Building | null>(null);
function newBuilding(): void {
  buildingDraft.value = { id: "", name: "", address: "" };
}
function editBuilding(row: Building): void {
  buildingDraft.value = { ...row };
}
function saveBuilding(): void {
  const d = buildingDraft.value;
  if (!d || !d.name.trim()) return;
  if (d.id) {
    catalog.buildings.value = catalog.buildings.value.map((b) =>
      b.id === d.id ? { ...d, name: d.name.trim(), address: d.address.trim() } : b,
    );
  } else {
    catalog.buildings.value = [
      ...catalog.buildings.value,
      { ...d, id: createEntityId(), name: d.name.trim(), address: d.address.trim() },
    ];
  }
  buildingDraft.value = null;
}
function cancelBuilding(): void {
  buildingDraft.value = null;
}
function removeBuilding(id: string): void {
  const x = catalog.buildings.value.find((b) => b.id === id);
  if (!x || !confirmDelete(x.name)) return;
  catalog.buildings.value = catalog.buildings.value.filter((b) => b.id !== id);
}

const departmentDraft = ref<Department | null>(null);
function newDepartment(): void {
  departmentDraft.value = { id: "", name: "", facultyId: catalog.faculties.value[0]?.id ?? "" };
}
function editDepartment(row: Department): void {
  departmentDraft.value = { ...row };
}
function saveDepartment(): void {
  const d = departmentDraft.value;
  if (!d || !d.name.trim() || !d.facultyId) return;
  if (d.id) {
    catalog.departments.value = catalog.departments.value.map((x) =>
      x.id === d.id ? { ...d, name: d.name.trim() } : x,
    );
  } else {
    catalog.departments.value = [...catalog.departments.value, { ...d, id: createEntityId(), name: d.name.trim() }];
  }
  departmentDraft.value = null;
}
function cancelDepartment(): void {
  departmentDraft.value = null;
}
function removeDepartment(id: string): void {
  const x = catalog.departments.value.find((d) => d.id === id);
  if (!x || !confirmDelete(x.name)) return;
  catalog.departments.value = catalog.departments.value.filter((d) => d.id !== id);
}

const groupDraft = ref<Group | null>(null);
function newGroup(): void {
  groupDraft.value = { id: "", name: "", facultyId: catalog.faculties.value[0]?.id ?? "" };
}
function editGroup(row: Group): void {
  groupDraft.value = { ...row };
}
function saveGroup(): void {
  const d = groupDraft.value;
  if (!d || !d.name.trim()) return;
  if (d.id) {
    catalog.groups.value = catalog.groups.value.map((x) => (x.id === d.id ? { ...d, name: d.name.trim() } : x));
  } else {
    catalog.groups.value = [...catalog.groups.value, { ...d, id: createEntityId(), name: d.name.trim() }];
  }
  groupDraft.value = null;
}
function cancelGroup(): void {
  groupDraft.value = null;
}
function removeGroup(id: string): void {
  const x = catalog.groups.value.find((g) => g.id === id);
  if (!x || !confirmDelete(x.name)) return;
  catalog.groups.value = catalog.groups.value.filter((g) => g.id !== id);
}

const teacherDraft = ref<Teacher | null>(null);
function newTeacher(): void {
  teacherDraft.value = {
    id: "",
    lastName: "",
    firstName: "",
    patronymic: "",
    departmentId: catalog.departments.value[0]?.id ?? "",
  };
}
function editTeacher(row: Teacher): void {
  teacherDraft.value = { ...row };
}
function saveTeacher(): void {
  const d = teacherDraft.value;
  if (!d || !d.lastName.trim()) return;
  const row = {
    ...d,
    lastName: d.lastName.trim(),
    firstName: d.firstName.trim(),
    patronymic: d.patronymic.trim(),
  };
  if (d.id) {
    catalog.teachers.value = catalog.teachers.value.map((x) => (x.id === d.id ? row : x));
  } else {
    catalog.teachers.value = [...catalog.teachers.value, { ...row, id: createEntityId() }];
  }
  teacherDraft.value = null;
}
function cancelTeacher(): void {
  teacherDraft.value = null;
}
function removeTeacher(id: string): void {
  const x = catalog.teachers.value.find((t) => t.id === id);
  if (!x || !confirmDelete(teacherDisplayName(x))) return;
  catalog.teachers.value = catalog.teachers.value.filter((t) => t.id !== id);
}

const subjectDraft = ref<Subject | null>(null);
function newSubject(): void {
  subjectDraft.value = { id: "", name: "", code: "" };
}
function editSubject(row: Subject): void {
  subjectDraft.value = { ...row };
}
function saveSubject(): void {
  const d = subjectDraft.value;
  if (!d || !d.name.trim()) return;
  if (d.id) {
    catalog.subjects.value = catalog.subjects.value.map((x) =>
      x.id === d.id ? { ...d, name: d.name.trim(), code: d.code.trim() } : x,
    );
  } else {
    catalog.subjects.value = [
      ...catalog.subjects.value,
      { ...d, id: createEntityId(), name: d.name.trim(), code: d.code.trim() },
    ];
  }
  subjectDraft.value = null;
}
function cancelSubject(): void {
  subjectDraft.value = null;
}
function removeSubject(id: string): void {
  const x = catalog.subjects.value.find((s) => s.id === id);
  if (!x || !confirmDelete(x.name)) return;
  catalog.subjects.value = catalog.subjects.value.filter((s) => s.id !== id);
}

const auditoriumDraft = ref<Auditorium | null>(null);
function newAuditorium(): void {
  auditoriumDraft.value = {
    id: "",
    number: "",
    buildingId: catalog.buildings.value[0]?.id ?? "",
    capacity: null,
    note: "",
  };
}
function editAuditorium(row: Auditorium): void {
  auditoriumDraft.value = { ...row };
}
function saveAuditorium(): void {
  const d = auditoriumDraft.value;
  if (!d || !d.number.trim() || !d.buildingId) return;
  const cap =
    d.capacity === null || d.capacity === undefined || Number.isNaN(Number(d.capacity))
      ? null
      : Number(d.capacity);
  const row: Auditorium = {
    ...d,
    number: d.number.trim(),
    note: d.note.trim(),
    capacity: cap,
  };
  if (d.id) {
    catalog.auditoriums.value = catalog.auditoriums.value.map((x) => (x.id === d.id ? row : x));
  } else {
    catalog.auditoriums.value = [...catalog.auditoriums.value, { ...row, id: createEntityId() }];
  }
  auditoriumDraft.value = null;
}
function cancelAuditorium(): void {
  auditoriumDraft.value = null;
}
function removeAuditorium(id: string): void {
  const x = catalog.auditoriums.value.find((a) => a.id === id);
  if (!x || !confirmDelete(x.number)) return;
  catalog.auditoriums.value = catalog.auditoriums.value.filter((a) => a.id !== id);
}

const slotDraft = ref<TimeSlotRow | null>(null);
function newSlot(): void {
  const next =
    catalog.timeSlots.value.length > 0 ? Math.max(...catalog.timeSlots.value.map((t) => t.slot)) + 1 : 1;
  slotDraft.value = { id: "", slot: next, time: "" };
}
function editSlot(row: TimeSlotRow): void {
  slotDraft.value = { ...row };
}
function saveSlot(): void {
  const d = slotDraft.value;
  if (!d || !d.time.trim() || !Number.isFinite(d.slot) || d.slot < 1) return;
  if (d.id) {
    catalog.timeSlots.value = catalog.timeSlots.value
      .map((x) => (x.id === d.id ? { ...d, time: d.time.trim() } : x))
      .sort((a, b) => a.slot - b.slot);
  } else {
    catalog.timeSlots.value = [
      ...catalog.timeSlots.value,
      { ...d, id: createEntityId(), time: d.time.trim() },
    ].sort((a, b) => a.slot - b.slot);
  }
  slotDraft.value = null;
}
function cancelSlot(): void {
  slotDraft.value = null;
}
function removeSlot(id: string): void {
  const x = catalog.timeSlots.value.find((t) => t.id === id);
  if (!x || !confirmDelete(`${x.slot} пара`)) return;
  catalog.timeSlots.value = catalog.timeSlots.value.filter((t) => t.id !== id);
}

const weekDayDraft = ref<{ index: number | null; title: string } | null>(null);
function startEditWeekDay(index: number): void {
  weekDayDraft.value = { index, title: catalog.weekDays.value[index] ?? "" };
}
function saveWeekDay(): void {
  const d = weekDayDraft.value;
  if (!d || d.index === null || !d.title.trim()) return;
  const next = [...catalog.weekDays.value];
  next[d.index] = d.title.trim();
  catalog.weekDays.value = next;
  weekDayDraft.value = null;
}
function cancelWeekDay(): void {
  weekDayDraft.value = null;
}
function addWeekDay(): void {
  catalog.weekDays.value = [...catalog.weekDays.value, "Новый день"];
}
function removeWeekDay(index: number): void {
  const label = catalog.weekDays.value[index] ?? "";
  if (!label || !confirmDelete(label)) return;
  catalog.weekDays.value = catalog.weekDays.value.filter((_, i) => i !== index);
}

const calendarDraft = ref<CalendarEntry | null>(null);
function newCalendarEntry(): void {
  calendarDraft.value = { id: "", date: "", kind: "other", title: "" };
}
function editCalendarEntry(row: CalendarEntry): void {
  calendarDraft.value = { ...row };
}
function saveCalendarEntry(): void {
  const d = calendarDraft.value;
  if (!d || !d.date.trim() || !d.title.trim()) return;
  if (d.id) {
    catalog.calendar.value = catalog.calendar.value.map((x) =>
      x.id === d.id ? { ...d, date: d.date.trim(), title: d.title.trim() } : x,
    );
  } else {
    catalog.calendar.value = [
      ...catalog.calendar.value,
      { ...d, id: createEntityId(), date: d.date.trim(), title: d.title.trim() },
    ];
  }
  calendarDraft.value = null;
}
function cancelCalendarEntry(): void {
  calendarDraft.value = null;
}
function removeCalendarEntry(id: string): void {
  const x = catalog.calendar.value.find((c) => c.id === id);
  if (!x || !confirmDelete(x.title)) return;
  catalog.calendar.value = catalog.calendar.value.filter((c) => c.id !== id);
}

const userTypeDraft = ref<UserType | null>(null);
function newUserType(): void {
  userTypeDraft.value = { id: "", name: "", description: "" };
}
function editUserType(row: UserType): void {
  userTypeDraft.value = { ...row };
}
function saveUserType(): void {
  const d = userTypeDraft.value;
  if (!d || !d.name.trim()) return;
  if (d.id) {
    catalog.userTypes.value = catalog.userTypes.value.map((x) =>
      x.id === d.id ? { ...d, name: d.name.trim(), description: d.description.trim() } : x,
    );
  } else {
    catalog.userTypes.value = [
      ...catalog.userTypes.value,
      { ...d, id: createEntityId(), name: d.name.trim(), description: d.description.trim() },
    ];
  }
  userTypeDraft.value = null;
}
function cancelUserType(): void {
  userTypeDraft.value = null;
}
function removeUserType(id: string): void {
  const x = catalog.userTypes.value.find((u) => u.id === id);
  if (!x || !confirmDelete(x.name)) return;
  catalog.userTypes.value = catalog.userTypes.value.filter((u) => u.id !== id);
}
</script>

<template>
  <div class="catalog-layout">
    <nav class="catalog-nav" aria-label="Справочники">
      <button
        v-for="item in navItems"
        :key="item.id"
        type="button"
        class="btn nav-btn"
        :class="{ active: active === item.id }"
        @click="active = item.id"
      >
        {{ item.label }}
      </button>
    </nav>

    <div class="catalog-body">
      <div v-show="active === 'faculties'" class="catalog-section">
        <div class="section-head">
          <h3>Факультеты</h3>
          <button type="button" class="btn primary" @click="newFaculty">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Сокращение</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.faculties.value" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ row.shortName }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editFaculty(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeFaculty(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="facultyDraft" class="editor card">
          <h4>{{ facultyDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Название
              <input v-model="facultyDraft.name" type="text" />
            </label>
            <label class="field">
              Сокращение
              <input v-model="facultyDraft.shortName" type="text" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveFaculty">Сохранить</button>
            <button type="button" class="btn" @click="cancelFaculty">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'buildings'" class="catalog-section">
        <div class="section-head">
          <h3>Здания</h3>
          <button type="button" class="btn primary" @click="newBuilding">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Адрес</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.buildings.value" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ row.address }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editBuilding(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeBuilding(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="buildingDraft" class="editor card">
          <h4>{{ buildingDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Название
              <input v-model="buildingDraft.name" type="text" />
            </label>
            <label class="field">
              Адрес
              <input v-model="buildingDraft.address" type="text" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveBuilding">Сохранить</button>
            <button type="button" class="btn" @click="cancelBuilding">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'departments'" class="catalog-section">
        <div class="section-head">
          <h3>Подразделения</h3>
          <button type="button" class="btn primary" @click="newDepartment">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Факультет</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.departments.value" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ facultyById.get(row.facultyId)?.name ?? row.facultyId }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editDepartment(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeDepartment(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="departmentDraft" class="editor card">
          <h4>{{ departmentDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Название
              <input v-model="departmentDraft.name" type="text" />
            </label>
            <label class="field">
              Факультет
              <select v-model="departmentDraft.facultyId">
                <option v-for="f in catalog.faculties.value" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveDepartment">Сохранить</button>
            <button type="button" class="btn" @click="cancelDepartment">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'groups'" class="catalog-section">
        <div class="section-head">
          <h3>Группы</h3>
          <button type="button" class="btn primary" @click="newGroup">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Факультет</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.groups.value" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ facultyById.get(row.facultyId)?.name ?? row.facultyId }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editGroup(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeGroup(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="groupDraft" class="editor card">
          <h4>{{ groupDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Название
              <input v-model="groupDraft.name" type="text" />
            </label>
            <label class="field">
              Факультет
              <select v-model="groupDraft.facultyId">
                <option v-for="f in catalog.faculties.value" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveGroup">Сохранить</button>
            <button type="button" class="btn" @click="cancelGroup">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'teachers'" class="catalog-section">
        <div class="section-head">
          <h3>Преподаватели</h3>
          <button type="button" class="btn primary" @click="newTeacher">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ФИО</th>
                <th>Подразделение</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.teachers.value" :key="row.id">
                <td>{{ teacherDisplayName(row) }}</td>
                <td>{{ departmentById.get(row.departmentId)?.name ?? row.departmentId }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editTeacher(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeTeacher(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="teacherDraft" class="editor card">
          <h4>{{ teacherDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Фамилия
              <input v-model="teacherDraft.lastName" type="text" />
            </label>
            <label class="field">
              Имя / инициалы
              <input v-model="teacherDraft.firstName" type="text" />
            </label>
            <label class="field">
              Отчество
              <input v-model="teacherDraft.patronymic" type="text" />
            </label>
            <label class="field">
              Подразделение
              <select v-model="teacherDraft.departmentId">
                <option v-for="d in catalog.departments.value" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveTeacher">Сохранить</button>
            <button type="button" class="btn" @click="cancelTeacher">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'subjects'" class="catalog-section">
        <div class="section-head">
          <h3>Предметы</h3>
          <button type="button" class="btn primary" @click="newSubject">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Код</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.subjects.value" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ row.code }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editSubject(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeSubject(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="subjectDraft" class="editor card">
          <h4>{{ subjectDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Название
              <input v-model="subjectDraft.name" type="text" />
            </label>
            <label class="field">
              Код
              <input v-model="subjectDraft.code" type="text" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveSubject">Сохранить</button>
            <button type="button" class="btn" @click="cancelSubject">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'auditoriums'" class="catalog-section">
        <div class="section-head">
          <h3>Аудитории</h3>
          <button type="button" class="btn primary" @click="newAuditorium">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Номер</th>
                <th>Здание</th>
                <th>Вместимость</th>
                <th>Примечание</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.auditoriums.value" :key="row.id">
                <td>{{ row.number }}</td>
                <td>{{ buildingById.get(row.buildingId)?.name ?? row.buildingId }}</td>
                <td>{{ row.capacity === null ? "—" : row.capacity }}</td>
                <td>{{ row.note }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editAuditorium(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeAuditorium(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="auditoriumDraft" class="editor card">
          <h4>{{ auditoriumDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Номер
              <input v-model="auditoriumDraft.number" type="text" />
            </label>
            <label class="field">
              Здание
              <select v-model="auditoriumDraft.buildingId">
                <option v-for="b in catalog.buildings.value" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select>
            </label>
            <label class="field">
              Вместимость
              <input v-model.number="auditoriumDraft.capacity" type="number" min="0" placeholder="необязательно" />
            </label>
            <label class="field">
              Примечание
              <input v-model="auditoriumDraft.note" type="text" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveAuditorium">Сохранить</button>
            <button type="button" class="btn" @click="cancelAuditorium">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'timeSlots'" class="catalog-section">
        <div class="section-head">
          <h3>Временные слоты</h3>
          <button type="button" class="btn primary" @click="newSlot">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Номер пары</th>
                <th>Время</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.timeSlots.value" :key="row.id">
                <td>{{ row.slot }}</td>
                <td>{{ row.time }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editSlot(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeSlot(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="slotDraft" class="editor card">
          <h4>{{ slotDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Номер пары
              <input v-model.number="slotDraft.slot" type="number" min="1" />
            </label>
            <label class="field">
              Время (интервал)
              <input v-model="slotDraft.time" type="text" placeholder="09:00 - 10:30" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveSlot">Сохранить</button>
            <button type="button" class="btn" @click="cancelSlot">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'calendar'" class="catalog-section">
        <h3>Дни недели в сетке расписания</h3>
        <p class="hint">
          Эти названия используются в таблицах расписания. Их порядок совпадает с колонками слева направо.
        </p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>День</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="(day, idx) in catalog.weekDays.value" :key="`${idx}-${day}`">
                <td>{{ idx + 1 }}</td>
                <td>{{ day }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="startEditWeekDay(idx)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeWeekDay(idx)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="section-head">
          <button type="button" class="btn" @click="addWeekDay">Добавить день</button>
        </div>
        <div v-if="weekDayDraft" class="editor card">
          <h4>Редактирование дня недели</h4>
          <label class="field">
            Название
            <input v-model="weekDayDraft.title" type="text" />
          </label>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveWeekDay">Сохранить</button>
            <button type="button" class="btn" @click="cancelWeekDay">Отмена</button>
          </div>
        </div>

        <h3 class="block-title">События календаря</h3>
        <p class="hint">Праздники, переносы, сессия и другие отметки (дата в формате ГГГГ-ММ-ДД).</p>
        <div class="section-head">
          <button type="button" class="btn primary" @click="newCalendarEntry">Добавить событие</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>Тип</th>
                <th>Название</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.calendar.value" :key="row.id">
                <td>{{ row.date }}</td>
                <td>{{ row.kind }}</td>
                <td>{{ row.title }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editCalendarEntry(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeCalendarEntry(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="calendarDraft" class="editor card">
          <h4>{{ calendarDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Дата
              <input v-model="calendarDraft.date" type="date" />
            </label>
            <label class="field">
              Тип
              <select v-model="calendarDraft.kind">
                <option value="holiday">Выходной / праздник</option>
                <option value="transfer">Перенос</option>
                <option value="exam">Сессия / экзамен</option>
                <option value="other">Другое</option>
              </select>
            </label>
            <label class="field">
              Название
              <input v-model="calendarDraft.title" type="text" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveCalendarEntry">Сохранить</button>
            <button type="button" class="btn" @click="cancelCalendarEntry">Отмена</button>
          </div>
        </div>
      </div>

      <div v-show="active === 'userTypes'" class="catalog-section">
        <div class="section-head">
          <h3>Типы пользователей</h3>
          <button type="button" class="btn primary" @click="newUserType">Добавить</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Описание</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in catalog.userTypes.value" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ row.description }}</td>
                <td class="cell-actions">
                  <button type="button" class="btn-link" @click="editUserType(row)">Изменить</button>
                  <button type="button" class="btn-link danger" @click="removeUserType(row.id)">Удалить</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="userTypeDraft" class="editor card">
          <h4>{{ userTypeDraft.id ? "Редактирование" : "Новая запись" }}</h4>
          <div class="form-row">
            <label class="field">
              Название
              <input v-model="userTypeDraft.name" type="text" />
            </label>
            <label class="field wide">
              Описание
              <input v-model="userTypeDraft.description" type="text" />
            </label>
          </div>
          <div class="editor-actions">
            <button type="button" class="btn primary" @click="saveUserType">Сохранить</button>
            <button type="button" class="btn" @click="cancelUserType">Отмена</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.catalog-layout {
  display: grid;
  grid-template-columns: minmax(200px, 260px) 1fr;
  gap: 16px;
  align-items: start;
}

.catalog-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: sticky;
  top: 12px;
}

.nav-btn {
  text-align: left;
  justify-content: flex-start;
}

.catalog-body {
  min-width: 0;
}

.catalog-section h3 {
  margin: 0 0 10px;
  font-size: 18px;
}

.block-title {
  margin: 22px 0 10px;
}

.hint {
  margin: 0 0 12px;
  color: var(--admin-subtle-text);
  font-size: 14px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.table-wrap {
  overflow-x: auto;
  margin-bottom: 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: var(--admin-table-bg);
}

th,
td {
  border: 1px solid var(--admin-border);
  padding: 10px;
  text-align: left;
  vertical-align: top;
}

th {
  background: var(--admin-th-bg);
}

.cell-actions {
  white-space: nowrap;
}

.editor {
  margin-top: 12px;
}

.card {
  border: 1px solid var(--admin-card-border);
  border-radius: 10px;
  padding: 14px;
  background: var(--admin-card-bg);
}

.editor h4 {
  margin: 0 0 12px;
}

.form-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 700;
  min-width: 200px;
  flex: 1 1 200px;
}

.field.wide {
  flex: 2 1 320px;
}

.editor-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
}

input,
select {
  width: 100%;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid var(--admin-input-border);
  border-radius: 6px;
  color: var(--admin-input-color);
  background: var(--admin-input-bg);
}

.btn {
  border: 1px solid var(--admin-btn-border);
  background: var(--admin-btn-bg);
  color: inherit;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
}

.btn.primary {
  border-color: var(--admin-primary-bg);
  background: var(--admin-primary-bg);
  color: var(--admin-primary-color);
}

.btn.active {
  border-color: var(--admin-accent);
  background: var(--admin-btn-active-bg);
}

.btn-link {
  border: 0;
  background: transparent;
  color: var(--admin-link);
  cursor: pointer;
  padding: 0;
  font-weight: 700;
  text-decoration: underline;
}

.btn-link.danger {
  color: var(--admin-link-danger);
}

@media (max-width: 900px) {
  .catalog-layout {
    grid-template-columns: 1fr;
  }

  .catalog-nav {
    flex-direction: row;
    flex-wrap: wrap;
    position: static;
  }

  .nav-btn {
    flex: 1 1 auto;
  }
}
</style>
