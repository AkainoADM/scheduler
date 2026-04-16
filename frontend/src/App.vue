<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import api from "@/api/axios";

/* ---------- Types ---------- */
type TimeSlotRow = {
  id: number;
  slot: number;
  name?: string;
  start_time?: string;
  end_time?: string;
  time?: string;
};

type LessonRow = {
  id: string;
  day: string;
  slot: number;
  subject: string;
  group: string | number;
  teacher: string | number;
  room: string | number;
  scheduleItemId?: number;
  fixed?: boolean;
};

type LessonDraft = {
  subject: string;
  group: number | string;
  teacher: number | string;
  room: number | string;
  slot: number;
  day: string;
};

/* ---------- Reactive state (single declarations only) ---------- */
/* UI */
const isDarkTheme = ref(false);
const selectedUserRole = ref<string | null>(null);
const adminTab = ref("overview");
const selectedView = ref("student"); // student | teacher | room
const composeSubTab = ref<"edit" | "table">("edit"); // добавлено

/* catalogs */
const groups = ref<{ id: number; name: string }[]>([]);
const timeSlots = ref<TimeSlotRow[]>([]);
const teachers = ref<{ id: number; name: string }[]>([]);
const teachersCatalog = ref<{ id: number; name: string }[]>([]); // добавлено
const rooms = ref<{ id: number; name: string }[]>([]);
const subjectsCatalog = ref<{ id: number; name: string }[]>([]);
const auditoriums = ref<{ id: number; number?: string; name?: string }[]>([]);

/* misc */
const weekDays = ref<string[]>(["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]);

/* selection */
const selectedGroup = ref<number | null>(null);
const selectedTeacher = ref<number | null>(null);
const selectedRoom = ref<number | null>(null);
const selectedAdminGroup = ref<number | null>(null);

/* admin / draft */
const draft = ref<Partial<LessonDraft>>({ subject: "", group: "", teacher: "", room: "", slot: 0, day: "" });
const editingLessonId = ref<string | null>(null);
const adminError = ref<string | null>(null);

/* backend */
const backendError = ref<string | null>(null);
const backendLoading = ref(false);

/* generation */
const genStartDate = ref("");
const genEndDate = ref("");
const templateSampleId = ref<number | null>(null);

/* lessons */
const studentLessons = ref<LessonRow[]>([]);
const teacherLessons = ref<LessonRow[]>([]);
const roomLessons = ref<LessonRow[]>([]);

/* computed */
const adminGroupSelectOptions = computed(() => groups.value.map(g => ({ id: g.id, name: g.name })));

/* ---------- Helper functions used by template ---------- */
function getLesson(collection: LessonRow[], day: string, slot: number): LessonRow | null {
  return collection.find(l => l.day === day && l.slot === slot) ?? null;
}

function getLessonForGroup(groupId: number | null, day: string, slot: number): LessonRow | null {
  if (groupId == null) return null;
  return studentLessons.value.find(l => Number(l.group) === Number(groupId) && l.day === day && l.slot === slot) ?? null;
}

function teacherDisplayName(t: { id: number; name: string } | number | undefined) {
  if (typeof t === "number") return teachers.value.find(x => x.id === t)?.name ?? String(t);
  if (!t) return "—";
  return t.name;
}

/* UI actions (stubs) */
function startEdit(lesson: LessonRow) {
  editingLessonId.value = lesson.id;
  draft.value = {
    subject: lesson.subject,
    group: lesson.group,
    teacher: lesson.teacher,
    room: lesson.room,
    slot: lesson.slot,
    day: lesson.day
  };
}

async function confirmAndDelete(scheduleItemId: string | number) {
  try {
    await api.delete(`/schedule/item/${scheduleItemId}`);
    await loadLessons();
  } catch (e: any) {
    adminError.value = e?.response?.data?.detail ?? String(e);
  }
}

async function togglePin(lesson: LessonRow) {
  try {
    const id = lesson.scheduleItemId;
    if (!id) return;
    await api.post(`/schedule/item/${id}/toggle_pin`);
    await loadLessons();
  } catch (e) {
    console.error(e);
  }
}

async function saveDraft() {
  adminError.value = null;
  if (!draft.value.subject || !draft.value.group || !draft.value.teacher || !draft.value.room) {
    adminError.value = "Заполните предмет, группу, преподавателя и аудиторию.";
    return;
  }
  try {
    const lessonResp = await api.post("/schedule/lessons", {
      text: draft.value.subject,
      time_slot_id: draft.value.slot,
      date: draft.value.day
    });
    const lessonId = lessonResp.data?.id;
    if (!lessonId) throw new Error("Не удалось создать lesson");
    const aud = auditoriums.value.find(a => a.id === Number(draft.value.room) || a.number === draft.value.room || a.name === draft.value.room);
    await api.post("/schedule/item", {
      lesson_id: lessonId,
      audience_id: aud?.id ?? draft.value.room,
      date: draft.value.day,
      time_slot_id: draft.value.slot
    });
    await loadLessons();
    resetDraft();
  } catch (e: any) {
    adminError.value = e?.response?.data?.detail ?? String(e);
  }
}

function resetDraft() {
  draft.value = { subject: "", group: "", teacher: "", room: "", slot: 0, day: "" };
  editingLessonId.value = null;
  adminError.value = null;
}

/* ---------- Loaders ---------- */
async function loadCatalogs() {
  try {
    const [g, t, s, a] = await Promise.all([
      api.get("/groups"),
      api.get("/teachers"),
      api.get("/subjects"),
      api.get("/auditoriums")
    ]);
    groups.value = g.data ?? [];
    teachers.value = t.data ?? [];
    teachersCatalog.value = t.data ?? []; // синхронизируем
    subjectsCatalog.value = s.data ?? [];
    auditoriums.value = a.data ?? [];
  } catch (e) {
    console.error("loadCatalogs", e);
  }
}

async function loadTimeSlots() {
  try {
    const resp = await api.get("/time_slots");
    timeSlots.value = resp.data ?? [];
  } catch (e) {
    console.error("loadTimeSlots", e);
  }
}

async function loadLessons() {
  try {
    const groupId = selectedGroup.value ?? groups.value[0]?.id ?? null;
    if (!groupId) return;
    const resp = await api.get("/schedule/structured", { params: { group_id: groupId } });
    studentLessons.value = [];
    teacherLessons.value = [];
    roomLessons.value = [];
    const data = resp.data;
    if (Array.isArray(data?.dates)) {
      for (const d of data.dates) {
        for (const p of d.pairs ?? []) {
          const row: LessonRow = {
            id: String(p.lesson_id ?? p.schedule_item_id ?? `${d.date}-${p.slot}`),
            day: d.date,
            slot: p.slot,
            subject: p.subject_name ?? String(p.subject_id ?? ""),
            group: data.group_name ?? String(groupId),
            teacher: p.teacher_name ?? String(p.teacher_id ?? ""),
            room: p.audience_name ?? String(p.audience_id ?? ""),
            scheduleItemId: p.schedule_item_id,
            fixed: Boolean(p.is_pinned)
          };
          studentLessons.value.push(row);
          if (p.teacher_id) teacherLessons.value.push(row);
          if (p.audience_id) roomLessons.value.push(row);
        }
      }
    }
  } catch (e) {
    console.error("loadLessons", e);
  }
}

/* generation */
async function generateSchedule() {
  backendLoading.value = true;
  backendError.value = null;
  try {
    await api.post("/generator/generate", { start: genStartDate.value, end: genEndDate.value });
    await loadLessons();
  } catch (err: any) {
    backendError.value = err?.response?.data?.detail ?? String(err);
  } finally {
    backendLoading.value = false;
  }
}

async function createTemplate() {
  try {
    await api.post("/templates", { sample_id: templateSampleId.value });
  } catch (e) {
    console.error("createTemplate", e);
  }
}

/* lifecycle */
onMounted(async () => {
  await Promise.all([loadCatalogs(), loadTimeSlots()]);
  // loadLessons вызывай после выбора группы
});
</script>


<template>
  <main :class="['container', { dark: isDarkTheme }]">
    <header class="header-row">
      <h1>Расписание занятий университета</h1>
      <aside class="theme-switcher">
        <div class="theme-label">
          Тема:
        </div>
        <button
          class="theme-toggle"
          :class="{ active: isDarkTheme }"
          type="button"
          :aria-pressed="isDarkTheme"
          @click="isDarkTheme = !isDarkTheme"
        >
          <span class="theme-toggle-track">
            <span class="theme-toggle-thumb"></span>
          </span>
          <span class="theme-toggle-text">{{ isDarkTheme ? "Тёмная" : "Светлая" }}</span>
        </button>
      </aside>
    </header>
    <p class="subtitle">
      Можно посмотреть расписание по группе, по преподавателю или по аудитории.
    </p>

    <section class="panel user-panel">
      <h2>Выбор пользователя</h2>
      <label class="selector">
        Вы вошли как:
        <select v-model="selectedUserRole">
          <option value="viewer">Студент (просмотр)</option>
          <option value="admin">Администратор (составление)</option>
        </select>
      </label>
    </section>

    <section v-if="selectedUserRole === 'admin'" class="panel admin-tabs-panel">
      <h2>Админ-панель</h2>
      <div class="admin-tabs">
        <button
          type="button"
          class="btn"
          :class="{ active: adminTab === 'compose' }"
          @click="adminTab = 'compose'"
        >
          Составление
        </button>
        <button
          type="button"
          class="btn"
          :class="{ active: adminTab === 'preview' }"
          @click="adminTab = 'preview'"
        >
          Просмотр
        </button>
        <button
          type="button"
          class="btn"
          :class="{ active: adminTab === 'directories' }"
          @click="adminTab = 'directories'"
        >
          Справочники
        </button>
        <button
          type="button"
          class="btn"
          :class="{ active: adminTab === 'access' }"
          @click="adminTab = 'access'"
        >
          Пользователи и доступ
        </button>
      </div>
    </section>

    <template v-if="selectedUserRole === 'viewer' || adminTab === 'preview'">
      <section class="panel">
      <h2>Выбор расписания</h2>
      <label class="selector">
        Показать расписание для:
        <select v-model="selectedView">
          <option value="student">Студента</option>
          <option value="teacher">Преподавателя</option>
          <option value="room">Аудитории</option>
        </select>
      </label>
      </section>

      <section v-if="selectedView === 'student'" class="panel">
        <h2>Расписание студента</h2>
        <label class="selector">
          Выберите свою группу:
          <select v-model="selectedGroup">
            <option v-for="group in groups" :key="group" :value="group">{{ group }}</option>
          </select>
        </label>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Пара / Время</th>
                <th v-for="day in weekDays" :key="day">{{ day }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="timeSlot in timeSlots" :key="timeSlot.slot">
                <td class="time-cell">
                  <strong>{{ timeSlot.slot }} пара</strong>
                  <span>{{ timeSlot.time }}</span>
                </td>
                <td v-for="day in weekDays" :key="`${day}-${timeSlot.slot}`">
                  <template v-if="getLesson(studentLessons, day, timeSlot.slot)">
                    <div class="subject">{{ getLesson(studentLessons, day, timeSlot.slot)?.subject }}</div>
                    <div class="meta">{{ getLesson(studentLessons, day, timeSlot.slot)?.teacher }}</div>
                    <div class="meta">Аудитория {{ getLesson(studentLessons, day, timeSlot.slot)?.room }}</div>
                  </template>
                  <span v-else class="empty">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-else-if="selectedView === 'teacher'" class="panel">
        <h2>Расписание преподавателя</h2>
        <label class="selector">
          Выберите преподавателя:
          <select v-model="selectedTeacher">
            <option v-for="teacher in teachers" :key="teacher" :value="teacher">{{ teacher }}</option>
          </select>
        </label>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Пара / Время</th>
                <th v-for="day in weekDays" :key="day">{{ day }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="timeSlot in timeSlots" :key="timeSlot.slot">
                <td class="time-cell">
                  <strong>{{ timeSlot.slot }} пара</strong>
                  <span>{{ timeSlot.time }}</span>
                </td>
                <td v-for="day in weekDays" :key="`${day}-${timeSlot.slot}`">
                  <template v-if="getLesson(teacherLessons, day, timeSlot.slot)">
                    <div class="subject">{{ getLesson(teacherLessons, day, timeSlot.slot)?.subject }}</div>
                    <div class="meta">{{ getLesson(teacherLessons, day, timeSlot.slot)?.group }}</div>
                    <div class="meta">Аудитория {{ getLesson(teacherLessons, day, timeSlot.slot)?.room }}</div>
                  </template>
                  <span v-else class="empty">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-else class="panel">
        <h2>Расписание по аудитории</h2>
        <label class="selector">
          Выберите аудиторию:
          <select v-model="selectedRoom">
            <option v-for="room in rooms" :key="room" :value="room">{{ room }}</option>
          </select>
        </label>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Пара / Время</th>
                <th v-for="day in weekDays" :key="day">{{ day }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="timeSlot in timeSlots" :key="timeSlot.slot">
                <td class="time-cell">
                  <strong>{{ timeSlot.slot }} пара</strong>
                  <span>{{ timeSlot.time }}</span>
                </td>
                <td v-for="day in weekDays" :key="`${day}-${timeSlot.slot}`">
                  <template v-if="getLesson(roomLessons, day, timeSlot.slot)">
                    <div class="subject">{{ getLesson(roomLessons, day, timeSlot.slot)?.subject }}</div>
                    <div class="meta">Группа {{ getLesson(roomLessons, day, timeSlot.slot)?.group }}</div>
                    <div class="meta">{{ getLesson(roomLessons, day, timeSlot.slot)?.teacher }}</div>
                  </template>
                  <span v-else class="empty">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <section v-if="selectedUserRole === 'admin' && adminTab === 'directories'" class="panel admin-directories-panel">
      <h2>Справочники</h2>
      <p class="subtitle admin-directories-hint">
        Управление факультетами, зданиями, подразделениями, группами, преподавателями, предметами, аудиториями,
        временными слотами, календарём и типами пользователей.
      </p>
      <AdminCatalogsPanel />
    </section>

    <section v-if="selectedUserRole === 'admin' && adminTab === 'access'" class="panel admin-access-panel">
      <h2>Пользователи, роли и права доступа</h2>
      <p class="subtitle admin-access-hint">
        Создание учётных записей, набор ролей и привязка прав к ролям (в перспективе — проверка на сервере).
      </p>
      <AdminAccessPanel />
    </section>

    <section v-if="selectedUserRole === 'admin' && adminTab === 'compose'" class="panel admin-panel">
      <h2>Страница администратора: составление расписания</h2>

      <div class="admin-toolbar">
        <button type="button" class="btn" @click="generateSchedule">
          Сгенерировать расписание
        </button>
        <button type="button" class="btn" @click="createTemplate">
          Создать шаблон
        </button>
      </div>

      <div class="admin-generate-controls">
        <div class="form-row">
          <label class="field">
            Дата начала (ДД.ММ.ГГГГ)
            <input v-model="genStartDate" type="text" />
          </label>
          <label class="field">
            Дата окончания (ДД.ММ.ГГГГ)
            <input v-model="genEndDate" type="text" />
          </label>
          <label class="field">
            ID шаблона
            <input v-model.number="templateSampleId" type="number" />
          </label>
        </div>
        <div v-if="backendError" class="admin-error">{{ backendError }}</div>
        <div v-if="backendLoading" class="small">Загрузка...</div>
      </div>

      <div class="admin-subtabs">
        <button
          type="button"
          class="btn"
          :class="{ active: composeSubTab === 'edit' }"
          @click="composeSubTab = 'edit'"
        >
          Составление
        </button>
        <button
          type="button"
          class="btn"
          :class="{ active: composeSubTab === 'table' }"
          @click="composeSubTab = 'table'"
        >
          Таблица расписания
        </button>
      </div>

      <form v-if="composeSubTab === 'edit'" class="admin-form" @submit.prevent="saveDraft">
        <div class="form-row">
          <label class="field">
            День
            <select v-model="draft.day">
              <option v-for="d in weekDays" :key="d" :value="d">{{ d }}</option>
            </select>
          </label>
          <label class="field">
            Пара
            <select v-model.number="draft.slot">
              <option v-for="t in timeSlots" :key="t.slot" :value="t.slot">{{ t.slot }} пара</option>
            </select>
          </label>
        </div>

        <div class="form-row">
          <label class="field">
            Предмет
            <input v-model="draft.subject" type="text" list="subject-suggestions" />
            <datalist id="subject-suggestions">
              <option v-for="s in subjectsCatalog" :key="s.id" :value="s.name" />
            </datalist>
          </label>
          <label class="field">
            Группа
            <select v-model="draft.group">
              <option v-for="g in adminGroupSelectOptions" :key="`draft-${g}`" :value="g">{{ g }}</option>
            </select>
          </label>
        </div>

        <div class="form-row">
          <label class="field">
            Преподаватель
            <input v-model="draft.teacher" type="text" list="teacher-suggestions" />
            <datalist id="teacher-suggestions">
              <option v-for="t in teachersCatalog" :key="t.id" :value="teacherDisplayName(t)" />
            </datalist>
          </label>
          <label class="field">
            Аудитория
            <input v-model="draft.room" type="text" list="room-suggestions" />
            <datalist id="room-suggestions">
              <option v-for="a in auditoriums" :key="a.id" :value="a.number" />
            </datalist>
          </label>
        </div>

        <div v-if="adminError" class="admin-error">{{ adminError }}</div>

        <div class="form-actions">
          <button type="submit" class="btn primary">
            {{ editingLessonId ? "Сохранить" : "Добавить" }}
          </button>
          <button
            v-if="editingLessonId"
            type="button"
            class="btn"
            @click="resetDraft"
          >
            Отменить
          </button>
        </div>
      </form>

      <template v-else>
        <label class="selector admin-group-picker">
          Расписание группы:
          <select v-model="selectedAdminGroup" :disabled="!!editingLessonId">
            <option v-for="g in adminGroupSelectOptions" :key="g" :value="g">{{ g }}</option>
          </select>
        </label>

        <div class="admin-grid-by-groups">
        <div class="admin-group-block">
          <h3 class="admin-group-title">Группа {{ selectedAdminGroup }}</h3>
          <div class="table-wrapper">
            <table class="admin-group-table">
              <thead>
                <tr>
                  <th>Пара / Время</th>
                  <th v-for="day in weekDays" :key="`${selectedAdminGroup}-${day}`">{{ day }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="timeSlot in timeSlots" :key="`${selectedAdminGroup}-${timeSlot.slot}`">
                  <td class="time-cell">
                    <strong>{{ timeSlot.slot }} пара</strong>
                    <span>{{ timeSlot.time }}</span>
                  </td>
                  <td
                    v-for="day in weekDays"
                    :key="`${selectedAdminGroup}-${day}-${timeSlot.slot}`"
                    class="admin-cell"
                  >
                    <template
                      v-for="lesson in [getLessonForGroup(selectedAdminGroup, day, timeSlot.slot)]"
                      :key="lesson?.id ?? `empty-${selectedAdminGroup}-${day}-${timeSlot.slot}`"
                    >
                      <template v-if="lesson">
                        <div class="subject">
                          {{ lesson.subject }}
                          <span v-if="lesson.fixed" class="fixed-badge">фикс.</span>
                        </div>
                        <div class="meta">{{ lesson.teacher }}</div>
                        <div class="meta">Ауд. {{ lesson.room }}</div>
                        <div class="admin-cell-actions">
                          <button
                            v-if="typeof lesson.scheduleItemId !== 'number'"
                            type="button"
                            class="btn-link"
                            @click="startEdit(lesson)"
                          >
                            Изменить
                          </button>
                          <button
                            v-if="typeof lesson.scheduleItemId !== 'number'"
                            type="button"
                            class="btn-link danger"
                            @click="() => confirmAndDelete(lesson.id)"
                          >
                            Удалить
                          </button>
                          <button
                            type="button"
                            class="btn-link"
                            @click="() => togglePin(lesson)"
                          >
                            {{ lesson.fixed ? "Снять фиксацию" : "Зафиксировать пару" }}
                          </button>
                        </div>
                      </template>
                      <span v-else class="empty">—</span>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      </template>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  background: #ffffff;
  transition: background-color 0.2s ease;
}

:global(body.app-dark-theme) {
  background: #0b1219;
}

.container {
  max-width: 1150px;
  margin: 0 auto;
  padding: 24px;
  font-family: Arial, sans-serif;
  background: #ffffff;
  color: #202124;
  transition: background-color 0.2s ease, color 0.2s ease;
  /* Вложенные админ-формы (справочники, доступ): следуют переключателю темы */
  --admin-subtle-text: #5e6369;
  --admin-meta-text: #4a4d52;
  --admin-table-bg: #ffffff;
  --admin-th-bg: #ecf2f8;
  --admin-border: #d8dee6;
  --admin-card-bg: #ffffff;
  --admin-card-border: #d9e0e7;
  --admin-input-bg: #ffffff;
  --admin-input-border: #b9c4cf;
  --admin-input-color: #202124;
  --admin-btn-bg: #ffffff;
  --admin-btn-border: #b9c4cf;
  --admin-btn-active-bg: rgba(79, 140, 255, 0.12);
  --admin-primary-bg: #4f8cff;
  --admin-primary-color: #ffffff;
  --admin-link: #2b6cb0;
  --admin-link-danger: #c0392b;
  --admin-perm-bg: #fafbfd;
  --admin-perm-border: #e4eaf0;
  --admin-code-bg: #edf2f7;
  --admin-accent: #4f8cff;
}

h1 {
  margin: 0;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 8px;
}

.subtitle {
  margin: 0 0 24px;
  color: #4a4d52;
}

.panel {
  background: #f7f9fb;
  border: 1px solid #d9e0e7;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.user-panel h2,
.admin-panel h2,
.admin-tabs-panel h2 {
  margin: 0 0 12px;
}

.admin-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.admin-subtabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.admin-tabs-panel .admin-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.admin-tabs {
  margin-top: 8px;
}

.btn {
  border: 1px solid #b9c4cf;
  background: #ffffff;
  color: inherit;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
}

.btn:hover {
  filter: brightness(0.98);
}

.btn.active {
  border-color: #4f8cff;
  background: rgba(79, 140, 255, 0.12);
}

.btn.primary {
  border-color: #4f8cff;
  background: #4f8cff;
  color: #ffffff;
}

.btn-link {
  border: 0;
  background: transparent;
  color: #2b6cb0;
  cursor: pointer;
  padding: 0;
  font-weight: 700;
  text-decoration: underline;
}

.btn-link.danger {
  color: #c0392b;
}

.admin-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-group-picker {
  margin-bottom: 4px;
}

.admin-grid-by-groups {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.admin-group-title {
  margin: 0 0 10px;
  font-size: 18px;
}

.admin-cell-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.fixed-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: #ffe8b3;
  color: #8c5a00;
}

.admin-empty-hint {
  margin: 18px 0 0;
  color: #5e6369;
  font-weight: 600;
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
  min-width: 220px;
  flex: 1 1 220px;
}

input {
  width: 100%;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid #b9c4cf;
  border-radius: 6px;
  color: #202124;
  background: #ffffff;
}

.admin-error {
  color: #c0392b;
  font-weight: 700;
}

.form-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.small {
  color: #5e6369;
  font-size: 12px;
  margin-top: 4px;
}

td.actions {
  display: flex;
  gap: 14px;
  align-items: center;
  white-space: nowrap;
}

.theme-switcher {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f7f9fb;
  border: 1px solid #d9e0e7;
  border-radius: 10px;
  padding: 10px 12px;
}

.theme-label {
  font-weight: 600;
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 2px;
  border-radius: 999px;
}

.theme-toggle-track {
  width: 46px;
  height: 26px;
  background: #d5deea;
  border-radius: 999px;
  padding: 3px;
  transition: background-color 0.2s ease;
}

.theme-toggle-thumb {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  transform: translateX(0);
  transition: transform 0.2s ease;
}

.theme-toggle.active .theme-toggle-track {
  background: #4f8cff;
}

.theme-toggle.active .theme-toggle-thumb {
  transform: translateX(20px);
}

.theme-toggle-text {
  min-width: 70px;
  text-align: left;
  font-weight: 600;
}

.selector {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  font-weight: 600;
}

select {
  min-width: 180px;
  padding: 7px 10px;
  border: 1px solid #b9c4cf;
  border-radius: 6px;
  color: #202124;
  background: #ffffff;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
}

th,
td {
  border: 1px solid #d8dee6;
  padding: 10px;
  text-align: left;
  vertical-align: top;
  min-width: 135px;
}

th {
  background: #ecf2f8;
}

.time-cell {
  min-width: 150px;
}

.time-cell span {
  display: block;
  margin-top: 4px;
  color: #5e6369;
  font-size: 13px;
}

.subject {
  font-weight: 700;
  margin-bottom: 4px;
}

.meta {
  font-size: 13px;
  color: #4a4d52;
  margin-bottom: 2px;
}

.empty {
  color: #8f98a1;
}

.container.dark {
  background: #0f1720;
  color: #e6edf4;
  --admin-subtle-text: #b8c4d1;
  --admin-meta-text: #b8c4d1;
  --admin-table-bg: #131c25;
  --admin-th-bg: #1d2b38;
  --admin-border: #2b3a49;
  --admin-card-bg: #131c25;
  --admin-card-border: #2b3a49;
  --admin-input-bg: #0f1720;
  --admin-input-border: #3a4c5e;
  --admin-input-color: #e6edf4;
  --admin-btn-bg: #0f1720;
  --admin-btn-border: #3a4c5e;
  --admin-btn-active-bg: rgba(123, 177, 255, 0.14);
  --admin-primary-bg: #1e62ff;
  --admin-primary-color: #ffffff;
  --admin-link: #7bb1ff;
  --admin-link-danger: #ff7a7a;
  --admin-perm-bg: #17212b;
  --admin-perm-border: #2b3a49;
  --admin-code-bg: #1d2b38;
  --admin-accent: #7bb1ff;
}

.container.dark .subtitle {
  color: #b8c4d1;
}

.container.dark .panel {
  background: #17212b;
  border-color: #2b3a49;
}

.container.dark .theme-switcher {
  background: #17212b;
  border-color: #2b3a49;
}

.container.dark .theme-toggle-track {
  background: #3a4c5e;
}

.container.dark .theme-toggle.active .theme-toggle-track {
  background: #7bb1ff;
}

.container.dark table {
  background: #131c25;
}

.container.dark th,
.container.dark td {
  border-color: #2b3a49;
}

.container.dark th {
  background: #1d2b38;
}

.container.dark .meta,
.container.dark .time-cell span {
  color: #b8c4d1;
}

.container.dark .empty {
  color: #7f91a3;
}

.container.dark select {
  color: #e6edf4;
  background: #0f1720;
  border-color: #3a4c5e;
}

.container.dark select:disabled {
  opacity: 0.55;
}

.container.dark input {
  color: #e6edf4;
  background: #0f1720;
  border-color: #3a4c5e;
}

.container.dark .btn {
  background: #0f1720;
  border-color: #3a4c5e;
}

.container.dark .btn:hover {
  filter: brightness(1.1);
}

.container.dark .btn.primary {
  background: #1e62ff;
  border-color: #1e62ff;
}

.container.dark .btn.active {
  background: rgba(123, 177, 255, 0.14);
}

.container.dark .btn-link {
  color: #7bb1ff;
}

.container.dark .btn-link.danger {
  color: #ff7a7a;
}

.container.dark .admin-error {
  color: #ff7a7a;
}

.container.dark .fixed-badge {
  background: #ffda9e;
  color: #4a2f00;
}

.container.dark .admin-empty-hint {
  color: #b8c4d1;
}

.container.dark .small {
  color: #b8c4d1;
}

@media (max-width: 900px) {
  .container {
    padding: 16px;
  }

  .header-row {
    align-items: stretch;
  }

  h1 {
    font-size: 28px;
    line-height: 1.2;
  }

  .selector {
    font-size: 14px;
  }

  select {
    min-width: 150px;
  }

  th,
  td {
    min-width: 120px;
    padding: 8px;
    font-size: 14px;
  }

  .time-cell {
    min-width: 135px;
  }
}

@media (max-width: 640px) {
  .container {
    padding: 12px;
  }

  .header-row {
    flex-direction: column;
    gap: 10px;
  }

  .theme-switcher {
    width: 100%;
    align-self: flex-start;
    justify-content: space-between;
  }

  h1 {
    font-size: 24px;
  }

  .subtitle {
    margin-bottom: 16px;
    font-size: 14px;
  }

  .panel {
    padding: 12px;
    margin-bottom: 14px;
  }

  .selector {
    width: 100%;
    flex-wrap: wrap;
    gap: 6px;
  }

  select {
    width: 100%;
    min-width: 0;
  }

  input {
    width: 100%;
  }

  th,
  td {
    min-width: 110px;
    font-size: 13px;
  }

  .subject {
    font-size: 13px;
  }

  .meta,
  .time-cell span {
    font-size: 12px;
  }

  td.actions {
    white-space: normal;
    flex-wrap: wrap;
  }
}
</style>
