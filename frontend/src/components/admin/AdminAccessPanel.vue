<script setup lang="ts">
import { computed, inject, ref } from "vue";
import type { AppUser, Permission, Role } from "../../domain/types";
import { catalogStateKey } from "../../domain/types";
import { createEntityId } from "../../utils/id";

const catalog = inject(catalogStateKey)!;

type AccessTab = "users" | "roles" | "permissions";
const tab = ref<AccessTab>("users");

const permissionById = computed(() => new Map(catalog.permissions.value.map((p) => [p.id, p])));
const roleById = computed(() => new Map(catalog.roles.value.map((r) => [r.id, r])));
const userTypeById = computed(() => new Map(catalog.userTypes.value.map((u) => [u.id, u])));

function confirmDelete(label: string): boolean {
  return window.confirm(`Удалить «${label}»?`);
}

/* Пользователи */
const userDraft = ref<AppUser | null>(null);
function newUser(): void {
  userDraft.value = {
    id: "",
    login: "",
    displayName: "",
    email: "",
    roleId: catalog.roles.value[0]?.id ?? "",
    active: true,
  };
}
function editUser(row: AppUser): void {
  userDraft.value = { ...row };
}
function saveUser(): void {
  const d = userDraft.value;
  if (!d || !d.login.trim() || !d.displayName.trim() || !d.roleId) return;
  const row: AppUser = {
    ...d,
    login: d.login.trim(),
    displayName: d.displayName.trim(),
    email: d.email.trim(),
  };
  if (d.id) {
    catalog.users.value = catalog.users.value.map((x) => (x.id === d.id ? row : x));
  } else {
    catalog.users.value = [...catalog.users.value, { ...row, id: createEntityId() }];
  }
  userDraft.value = null;
}
function cancelUser(): void {
  userDraft.value = null;
}
function removeUser(id: string): void {
  const x = catalog.users.value.find((u) => u.id === id);
  if (!x || !confirmDelete(x.login)) return;
  catalog.users.value = catalog.users.value.filter((u) => u.id !== id);
}

/* Роли */
const roleDraft = ref<Role | null>(null);
function newRole(): void {
  roleDraft.value = {
    id: "",
    name: "",
    userTypeId: catalog.userTypes.value[0]?.id ?? "",
    permissionIds: [],
  };
}
function editRole(row: Role): void {
  roleDraft.value = { ...row, permissionIds: [...row.permissionIds] };
}
function saveRole(): void {
  const d = roleDraft.value;
  if (!d || !d.name.trim() || !d.userTypeId) return;
  const row: Role = {
    ...d,
    name: d.name.trim(),
    permissionIds: [...new Set(d.permissionIds)],
  };
  if (d.id) {
    catalog.roles.value = catalog.roles.value.map((x) => (x.id === d.id ? row : x));
  } else {
    catalog.roles.value = [...catalog.roles.value, { ...row, id: createEntityId() }];
  }
  roleDraft.value = null;
}
function cancelRole(): void {
  roleDraft.value = null;
}
function removeRole(id: string): void {
  const x = catalog.roles.value.find((r) => r.id === id);
  if (!x || !confirmDelete(x.name)) return;
  if (catalog.users.value.some((u) => u.roleId === id)) {
    window.alert("Нельзя удалить роль: есть пользователи с этой ролью.");
    return;
  }
  catalog.roles.value = catalog.roles.value.filter((r) => r.id !== id);
}

function toggleRolePermission(permId: string): void {
  const d = roleDraft.value;
  if (!d) return;
  if (d.permissionIds.includes(permId)) {
    d.permissionIds = d.permissionIds.filter((x) => x !== permId);
  } else {
    d.permissionIds = [...d.permissionIds, permId];
  }
}

function rolePermissionLabel(role: Role): string {
  return role.permissionIds
    .map((id) => permissionById.value.get(id)?.label ?? id)
    .join(", ");
}

/* Права */
const permDraft = ref<Permission | null>(null);
function newPermission(): void {
  permDraft.value = { id: "", key: "", label: "" };
}
function editPermission(row: Permission): void {
  permDraft.value = { ...row };
}
function savePermission(): void {
  const d = permDraft.value;
  if (!d || !d.key.trim() || !d.label.trim()) return;
  const row: Permission = { ...d, key: d.key.trim(), label: d.label.trim() };
  if (d.id) {
    catalog.permissions.value = catalog.permissions.value.map((x) => (x.id === d.id ? row : x));
  } else {
    if (catalog.permissions.value.some((p) => p.key === row.key)) {
      window.alert("Ключ права должен быть уникальным.");
      permDraft.value = null;
      return;
    }
    catalog.permissions.value = [...catalog.permissions.value, { ...row, id: createEntityId() }];
  }
  permDraft.value = null;
}
function cancelPermission(): void {
  permDraft.value = null;
}
function removePermission(id: string): void {
  const x = catalog.permissions.value.find((p) => p.id === id);
  if (!x || !confirmDelete(x.label)) return;
  if (catalog.roles.value.some((r) => r.permissionIds.includes(id))) {
    window.alert("Нельзя удалить право: оно назначено одной или нескольким ролям.");
    return;
  }
  catalog.permissions.value = catalog.permissions.value.filter((p) => p.id !== id);
}
</script>

<template>
  <div class="access-panel">
    <div class="access-tabs">
      <button type="button" class="btn" :class="{ active: tab === 'users' }" @click="tab = 'users'">
        Пользователи
      </button>
      <button type="button" class="btn" :class="{ active: tab === 'roles' }" @click="tab = 'roles'">
        Роли
      </button>
      <button type="button" class="btn" :class="{ active: tab === 'permissions' }" @click="tab = 'permissions'">
        Права доступа
      </button>
    </div>

    <div v-show="tab === 'users'" class="tab-body">
      <div class="section-head">
        <h3>Пользователи</h3>
        <button type="button" class="btn primary" @click="newUser">Добавить</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Логин</th>
              <th>Имя</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Активен</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in catalog.users.value" :key="row.id">
              <td>{{ row.login }}</td>
              <td>{{ row.displayName }}</td>
              <td>{{ row.email }}</td>
              <td>{{ roleById.get(row.roleId)?.name ?? row.roleId }}</td>
              <td>{{ row.active ? "да" : "нет" }}</td>
              <td class="cell-actions">
                <button type="button" class="btn-link" @click="editUser(row)">Изменить</button>
                <button type="button" class="btn-link danger" @click="removeUser(row.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="userDraft" class="editor card">
        <h4>{{ userDraft.id ? "Редактирование" : "Новый пользователь" }}</h4>
        <div class="form-row">
          <label class="field">
            Логин
            <input v-model="userDraft.login" type="text" autocomplete="off" />
          </label>
          <label class="field">
            Отображаемое имя
            <input v-model="userDraft.displayName" type="text" />
          </label>
          <label class="field">
            Email
            <input v-model="userDraft.email" type="email" />
          </label>
          <label class="field">
            Роль
            <select v-model="userDraft.roleId">
              <option v-for="r in catalog.roles.value" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
          </label>
          <label class="field checkbox-field">
            <span>Активен</span>
            <input v-model="userDraft.active" type="checkbox" />
          </label>
        </div>
        <div class="editor-actions">
          <button type="button" class="btn primary" @click="saveUser">Сохранить</button>
          <button type="button" class="btn" @click="cancelUser">Отмена</button>
        </div>
      </div>
    </div>

    <div v-show="tab === 'roles'" class="tab-body">
      <div class="section-head">
        <h3>Роли</h3>
        <button type="button" class="btn primary" @click="newRole">Добавить</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Название</th>
              <th>Тип пользователя</th>
              <th>Права</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in catalog.roles.value" :key="row.id">
              <td>{{ row.name }}</td>
              <td>{{ userTypeById.get(row.userTypeId)?.name ?? row.userTypeId }}</td>
              <td class="perms-cell">{{ rolePermissionLabel(row) }}</td>
              <td class="cell-actions">
                <button type="button" class="btn-link" @click="editRole(row)">Изменить</button>
                <button type="button" class="btn-link danger" @click="removeRole(row.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="roleDraft" class="editor card">
        <h4>{{ roleDraft.id ? "Редактирование роли" : "Новая роль" }}</h4>
        <div class="form-row">
          <label class="field">
            Название
            <input v-model="roleDraft.name" type="text" />
          </label>
          <label class="field">
            Тип пользователя
            <select v-model="roleDraft.userTypeId">
              <option v-for="u in catalog.userTypes.value" :key="u.id" :value="u.id">{{ u.name }}</option>
            </select>
          </label>
        </div>
        <div class="perm-grid">
          <div v-for="p in catalog.permissions.value" :key="p.id" class="perm-row">
            <label class="perm-check">
              <input
                type="checkbox"
                :checked="roleDraft.permissionIds.includes(p.id)"
                @change="toggleRolePermission(p.id)"
              />
              <span>
                <strong>{{ p.label }}</strong>
                <span class="perm-key">{{ p.key }}</span>
              </span>
            </label>
          </div>
        </div>
        <div class="editor-actions">
          <button type="button" class="btn primary" @click="saveRole">Сохранить</button>
          <button type="button" class="btn" @click="cancelRole">Отмена</button>
        </div>
      </div>
    </div>

    <div v-show="tab === 'permissions'" class="tab-body">
      <div class="section-head">
        <h3>Права доступа</h3>
        <button type="button" class="btn primary" @click="newPermission">Добавить</button>
      </div>
      <p class="hint">
        Ключ используется в коде и API (например, <code>schedule.edit</code>). Подпись видна администраторам.
      </p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Ключ</th>
              <th>Подпись</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in catalog.permissions.value" :key="row.id">
              <td><code>{{ row.key }}</code></td>
              <td>{{ row.label }}</td>
              <td class="cell-actions">
                <button type="button" class="btn-link" @click="editPermission(row)">Изменить</button>
                <button type="button" class="btn-link danger" @click="removePermission(row.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="permDraft" class="editor card">
        <h4>{{ permDraft.id ? "Редактирование" : "Новое право" }}</h4>
        <div class="form-row">
          <label class="field">
            Ключ (латиница, точки)
            <input v-model="permDraft.key" type="text" :disabled="!!permDraft.id" />
          </label>
          <label class="field">
            Подпись
            <input v-model="permDraft.label" type="text" />
          </label>
        </div>
        <div class="editor-actions">
          <button type="button" class="btn primary" @click="savePermission">Сохранить</button>
          <button type="button" class="btn" @click="cancelPermission">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.access-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.access-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tab-body h3 {
  margin: 0;
  font-size: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.hint {
  margin: 0 0 12px;
  color: var(--admin-subtle-text);
  font-size: 14px;
}

.hint code {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.92em;
  background: var(--admin-code-bg);
  color: inherit;
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

.perms-cell {
  max-width: 380px;
  font-size: 13px;
  color: var(--admin-meta-text);
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

.checkbox-field {
  flex: 0 0 auto;
  min-width: 120px;
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.checkbox-field input {
  width: auto;
}

.perm-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.perm-row {
  padding: 8px 10px;
  border: 1px solid var(--admin-perm-border);
  border-radius: 8px;
  background: var(--admin-perm-bg);
}

.perm-check {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  cursor: pointer;
  font-weight: 600;
}

.perm-check input {
  margin-top: 3px;
}

.perm-key {
  display: block;
  font-weight: 500;
  font-size: 12px;
  color: var(--admin-subtle-text);
  margin-top: 4px;
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
</style>
