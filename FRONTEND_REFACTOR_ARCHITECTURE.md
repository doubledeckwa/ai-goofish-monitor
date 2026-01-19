# Vue 3 Front-end reconstruction architecture plan (v1.1)

## 0. Background and principles

This document is intended for `ai-goofish-monitor` The front-end reconstruction of the project provides a complete engineering architecture solution. This solution is based on an existing backend（FastAPI）and front-end (native JavaScript）In-depth analysis of the code and strict adherence to the following core principles：

1.  **Complexity Equivalence**: Ensure the complexity of the front-end architecture matches the simplicity of the back-end services to avoid over-design。
2.  **Maintainability first**: Outputs are easy to understand and easy to take over、Easily extensible code。
3.  **business driven**: Any introduced complexity (e.g. WebSocket、RBAC）All must be supported by clear business or future functional requirements.。

---

## 1. Module split structure (Logical Modules)

The application will be logically split by functional areas, with each module containing its own independent view、Routing, stateful logic and components。

-   **`Auth` (Authentication module)**
-   **`Tasks` (Task management module)**
-   **`Results` (Results viewing module)**
-   **`Logs` (Log module)**
-   **`Settings` (System settings module)**
-   **`Dashboard` (Dashboard module)** - *Reserved for the future*
-   **`Core` (core/shared module)**

---

## 2. Page routing tree (Vue Router)

Routing design will follow modularity and be reserved for future permission control `meta` Field。

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/tasks',
    children: [
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/TasksView.vue'),
        meta: { title: 'task management', requiresAuth: true },
      },
      // ... Other sub-routes
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// ... route guard
export default router;
```

---

## 3. State management design (Composables)

Based on Vue 3 Composition API of **Composable** The function performs state management and abandons the introduction. Pinia，to reduce complexity。

-   **`useWebSocket.ts`**: unique and central WebSocket Manager, encapsulating connections、Reconnection and message distribution。
-   **`useAuth.ts`**: Manage the status and permissions of the current user for RBAC provide the basis。
-   **`useTasks.ts`**: encapsulation `Tasks` All business logic of the module and response WebSocket Push。
-   **`useLogs.ts`**: encapsulation `Logs` module business logic and response WebSocket Push。

---

## 4. UI Build plan (UI Implementation Strategy)

we will use **`shadcn-vue`** as UI construction plan。

-   **core concept**: `shadcn-vue` **Not a component library**，Rather, it is a series of reusable components**code collection**。through which we CLI Copy component source code directly into the project。
-   **technology stack**:
    -   **style**: **Tailwind CSS**。All components are built based on their atomic class names, providing maximum style control。
    -   **Ground floor**: **Radix Vue**。Provides headless（headless）、Fully functional and highly consistent WAI-ARIA Standard low-level component primitives。
-   **Implications**:
    -   **Component ownership**: us 100% Has component code that can be modified at will to meet design needs，No need to override the library's styles。
    -   **Maintainability**: Since the code is local, tracing and debugging component behavior becomes very straightforward。
    -   **Packing volume**: The final product contains only the actual code and styles used, and is smaller in size。
    -   **development process**: Initial setup (such as configuring Tailwind）It will be slightly more complicated than using a traditional component library, but subsequent development and customization will be more efficient.。

---

## 5. Interface alignment table (API Alignment)

| module | Function | HTTP method | API Endpoint | Vue call function |
| :--- | :--- | :--- | :--- | :--- |
| **Tasks** | Get all tasks | `GET` | `/api/tasks` | `api.tasks.getAll()` |
| | AI 创建任务 | `POST` | `/api/tasks/generate` | `api.tasks.createWithAI()` |
| | ... | ... | ... | ... |
| **Results** | Get result file list | `GET` | `/api/results/files` | `api.results.getFiles()` |
| | ... | ... | ... | ... |
| **Logs** | Get log | `GET` | `/api/logs` | `api.logs.get()` |
| | ... | ... | ... | ... |
| **Settings**| Get system status | `GET` | `/api/settings/status` | `api.settings.getStatus()` |
| | ... | ... | ... | ... |

*(Table content and v1.0 Version consistent)*

---

## 6. Directory structure

new `web-ui` The directory will adopt a function-driven and hierarchical structure。

```
web-ui/
├── src/
│   ├── api/             # API request layer
│   ├── assets/          # Static resources
│   ├── components/      # overall and shadcn-vue Generated components
│   │   ├── ui/          #   - shadcn-vue generated UI components (e.g., button.vue, dialog.vue)
│   │   └── common/      #   - Common business components of the project itself
│   ├── composables/     # State and business logic
│   ├── layouts/         # Page main layout
│   ├── router/          # Routing configuration
│   ├── services/        # Core services (e.g., websocket.ts)
│   ├── lib/             # Tailwind CSS Related tools (e.g., utils.ts)
│   ├── types/           # TypeScript type definition
│   └── views/           # Page-level view components
├── tailwind.config.js   # Tailwind CSS Configuration file
├── components.json      # shadcn-vue Configuration file
├── vite.config.ts
└── package.json
```

---

## 7. Component design boundaries

Components will be strictly divided into "container components"”and "display component”。

-   **`TasksView.vue` (container/view component)**
    -   **Responsibilities**: Page entry, call `useTasks()` Get data and methods and pass them to child components。
    -   **internal**: `const { tasks, isLoading, createTask } = useTasks();`

-   **`TasksTable.vue` (Presentation component)**
    -   **Responsibilities**: Receive task list and use `shadcn-vue` of `Table` The component is rendered. When the user operates，**Only emit events**。
    -   **Props**: `tasks: Task[]`, `isLoading: boolean`。
    -   **Emits**: `@edit-task`, `@delete-task`, `@run-task`, `@stop-task`。

-   **`TaskFormWizard.vue` (container/Functional components)**
    -   **Responsibilities**: To implement a multi-step guided process for task creation, use `shadcn-vue` of `Dialog`, `Input`, `Button` Build other components。
    -   **Props**: `initialData?: Task`。
    -   **Emits**: `@save`。

---

## 8. Decoupling explanation of rendering layer and business layer

The core idea is**Clean separation of rendering, business logic and data requests**。

1.  **render layer (Views & Components)**:
    -   **Role**: “Dumb” component。He is only responsible for "what to look at"”。
    -   **accomplish**: use Vue Template syntax、**Depend on `shadcn-vue` Generated and maintained by us UI components**as well as **Tailwind CSS** Class name. take over `props` The data is rendered via `emits` Report user interactions。

2.  **business logic layer (Composables)**:
    -   **Role**: “"Smart" coordinator。Responsible for "what to do"”。
    -   **accomplish**: `use...` function. They are responsive、Stateful logic unit, responsible for calling API、Process data and expose it to the rendering layer。

3.  **Data service layer (API & Services)**:
    -   **Role**: Data porter”。Responsible for “where to get data from””。
    -   **accomplish**: exist `src/api` Typed under directory API request function, and `src/services` down WebSocket Serve。

#### Data flow example (One-way data flow):

`The user clicks "Delete”button` -> `TaskTableRow.vue` **emits** `@delete` event -> `TasksView.vue` Listen to the event and call `useTasks()` provided `deleteTask(id)` method -> `useTasks.ts` call `api.tasks.delete(id)` -> `api/tasks.ts` issue `fetch` ask -> after success `useTasks.ts` update internal `tasks` ref -> `TasksView.vue` automatic response `tasks` changes and re-renders `TasksTable.vue`。
